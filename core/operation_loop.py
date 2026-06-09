import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict
from loguru import logger
from .nuclear_intelligence import (
    NuclearIntelligenceCore,
    ResearchQuestion,
    ResearchAnswer,
    EvaluationScore
)
from blockchain.virtual_ledger import VirtualLedger

class OperationLoopConfig:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.interval_minutes = config.get("scheduler_interval_minutes", 45)
        self.min_accuracy_threshold = config.get("min_accuracy_threshold", 93.0)
        self.min_novelty_threshold = config.get("min_novelty_threshold", 70.0)
        self.questions_per_cycle = config.get("questions_per_cycle", 3)

class OperationLoop:
    def __init__(self, ni_core: NuclearIntelligenceCore, ledger: VirtualLedger, config: Dict[str, Any]):
        self.ni_core = ni_core
        self.ledger = ledger
        self.config = OperationLoopConfig(config)
        self.logger = logger
        self.cycle_count = 0
        self.cycle_history = []
        self.execution_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_questions_generated": 0,
            "total_answers_generated": 0,
            "total_tokens_minted": 0,
            "average_accuracy": 0.0
        }

    async def execute_cycle(self) -> Dict[str, Any]:
        self.logger.info(f"Starting operation cycle #{self.cycle_count + 1}")
        cycle_start_time = datetime.now()
        cycle_report = {
            "cycle_number": self.cycle_count + 1,
            "start_time": cycle_start_time.isoformat(),
            "questions": [],
            "answers": [],
            "evaluations": [],
            "tokens_minted": [],
            "errors": [],
            "status": "in_progress"
        }

        try:
            questions = await self.ni_core.generate_complex_questions(num_questions=self.config.questions_per_cycle)
            cycle_report["questions"] = [asdict(q) for q in questions]
            self.execution_stats["total_questions_generated"] += len(questions)

            total_acc = 0
            acc_count = 0

            for question in questions:
                try:
                    answer = await self.ni_core.conduct_deep_research(question)
                    evaluation_scores = await self.ni_core.evaluate_answer(answer)
                    answer.evaluation_scores = evaluation_scores
                    
                    cycle_report["answers"].append(asdict(answer))
                    cycle_report["evaluations"].append(evaluation_scores.dict())
                    
                    total_acc += evaluation_scores.scientific_accuracy
                    acc_count += 1

                    if (evaluation_scores.scientific_accuracy >= self.config.min_accuracy_threshold and
                        evaluation_scores.novelty_score >= self.config.min_novelty_threshold):
                        
                        mint_result = self.ledger.mint_nes_token(
                            answer_id=answer.id,
                            question=question.question,
                            answer=answer.answer,
                            evaluation_scores=evaluation_scores.dict(),
                            answer_metadata=asdict(answer)
                        )
                        cycle_report["tokens_minted"].append(mint_result)
                        self.execution_stats["total_tokens_minted"] += 1
                        self.ni_core.add_to_knowledge_base(answer)
                    
                    self.execution_stats["total_answers_generated"] += 1
                except Exception as e:
                    self.logger.error(f"Error in question processing: {e}")
                    cycle_report["errors"].append(str(e))

            if acc_count > 0:
                current_avg = total_acc / acc_count
                prev_total = self.execution_stats["average_accuracy"] * (self.execution_stats["successful_cycles"])
                self.execution_stats["average_accuracy"] = (prev_total + current_avg) / (self.execution_stats["successful_cycles"] + 1)

            self.ledger.mine_pending_block()
            
            cycle_report["status"] = "completed"
            cycle_report["end_time"] = datetime.now().isoformat()
            self.execution_stats["successful_cycles"] += 1
            self.execution_stats["total_cycles"] += 1
            self.cycle_count += 1
            self.cycle_history.append(cycle_report)

            # Save reports
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            with open(reports_dir / f"cycle_{self.cycle_count}.json", "w") as f:
                json.dump(cycle_report, f, indent=4)
            
            return cycle_report
        except Exception as e:
            self.logger.error(f"Cycle failed: {e}")
            cycle_report["status"] = "failed"
            cycle_report["errors"].append(str(e))
            self.execution_stats["failed_cycles"] += 1
            self.execution_stats["total_cycles"] += 1
            return cycle_report

    def generate_cycle_report(self, cycle_report: Dict[str, Any]) -> str:
        report = f"### ⚛️ Nuclear Intelligence Cycle #{cycle_report['cycle_number']} Report\n\n"
        report += f"**Status:** {cycle_report['status']}\n"
        report += f"**Start Time:** {cycle_report['start_time']}\n"
        report += f"**Questions Generated:** {len(cycle_report['questions'])}\n"
        report += f"**NES Tokens Minted:** {len(cycle_report['tokens_minted'])}\n\n"
        
        if cycle_report.get('tokens_minted'):
            report += "#### 🪙 Newly Minted NES Tokens:\n"
            for mint in cycle_report['tokens_minted']:
                token = mint['token_data']
                report += f"- **Token ID:** {mint['tx_id'][:12]}... | **Accuracy:** {token['evaluation_scores']['scientific_accuracy']}% | **Novelty:** {token['evaluation_scores']['novelty_score']}%\n"
        
        if cycle_report.get('errors'):
            report += "\n#### ⚠️ Errors Encountered:\n"
            for error in cycle_report['errors']:
                report += f"- {error}\n"
                
        return report

    async def run_continuous(self, max_cycles: Optional[int] = None) -> None:
        while max_cycles is None or self.cycle_count < max_cycles:
            await self.execute_cycle()
            await asyncio.sleep(self.config.interval_minutes * 60)

    def get_execution_stats(self) -> Dict[str, Any]:
        return {
            **self.execution_stats,
            "last_cycle_time": self.cycle_history[-1]["end_time"] if self.cycle_history else None
        }
