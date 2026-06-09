"""
Nuclear Intelligence Operation Loop
Main automated loop that executes the complete research cycle:
1. Generate complex questions
2. Conduct deep research
3. Multi-layer evaluation
4. NES token minting
5. Knowledge base update
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict

from loguru import logger

from nuclear_intelligence import (
    NuclearIntelligenceCore,
    ResearchQuestion,
    ResearchAnswer,
    EvaluationScore
)
from blockchain.virtual_ledger import VirtualLedger, TransactionType


class OperationLoopConfig:
    """Configuration for the operation loop."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.interval_minutes = config.get("scheduler_interval_minutes", 45)
        self.min_accuracy_threshold = config.get("min_accuracy_threshold", 93.0)
        self.min_novelty_threshold = config.get("min_novelty_threshold", 70.0)
        self.questions_per_cycle = config.get("questions_per_cycle", 3)
        self.enable_human_review = config.get("feature_human_in_the_loop", True)


class OperationLoop:
    """
    Main operation loop for Nuclear Intelligence system.
    Orchestrates the complete research-to-tokenization pipeline.
    """
    
    def __init__(self, ni_core: NuclearIntelligenceCore, ledger: VirtualLedger,
                 config: Dict[str, Any]):
        """Initialize the operation loop."""
        self.ni_core = ni_core
        self.ledger = ledger
        self.config = OperationLoopConfig(config)
        self.logger = logger
        
        self.cycle_count = 0
        self.cycle_history: List[Dict[str, Any]] = []
        self.execution_stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_questions_generated": 0,
            "total_answers_generated": 0,
            "total_tokens_minted": 0,
            "average_accuracy": 0.0
        }
        
        self.logger.info("Operation Loop initialized")
    
    async def execute_cycle(self) -> Dict[str, Any]:
        """
        Execute one complete cycle of the operation loop.
        
        Steps:
        1. Generate complex questions
        2. Conduct deep research for each question
        3. Evaluate answers
        4. Mint NES tokens for approved answers
        5. Update knowledge base
        6. Mine block
        """
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
            # Step 1: Generate Complex Questions
            self.logger.info("Step 1: Generating complex questions...")
            questions = await self.ni_core.generate_complex_questions(
                num_questions=self.config.questions_per_cycle
            )
            
            cycle_report["questions"] = [
                {
                    "id": q.id,
                    "question": q.question,
                    "category": q.category.value,
                    "complexity": q.complexity_level,
                    "keywords": q.keywords
                }
                for q in questions
            ]
            
            self.execution_stats["total_questions_generated"] += len(questions)
            
            # Step 2-5: Research, Evaluate, and Mint for each question
            for question in questions:
                try:
                    self.logger.info(f"Processing question: {question.question[:100]}...")
                    
                    # Step 2: Conduct Deep Research
                    self.logger.info("Step 2: Conducting deep research...")
                    answer = await self.ni_core.conduct_deep_research(question)
                    
                    cycle_report["answers"].append({
                        "id": answer.id,
                        "question_id": answer.question_id,
                        "answer_preview": answer.answer[:200],
                        "sources_count": len(answer.sources),
                        "equations_count": len(answer.equations)
                    })
                    
                    # Step 3: Evaluate Answer
                    self.logger.info("Step 3: Evaluating answer...")
                    evaluation_scores = await self.ni_core.evaluate_answer(answer)
                    
                    cycle_report["evaluations"].append({
                        "answer_id": answer.id,
                        "scientific_accuracy": evaluation_scores.scientific_accuracy,
                        "novelty_score": evaluation_scores.novelty_score,
                        "usefulness_score": evaluation_scores.usefulness_score,
                        "self_consistency": evaluation_scores.self_consistency,
                        "overall_score": evaluation_scores.overall_score
                    })
                    
                    # Check approval criteria
                    if (evaluation_scores.scientific_accuracy >= self.config.min_accuracy_threshold and
                        evaluation_scores.novelty_score >= self.config.min_novelty_threshold):
                        
                        self.logger.info("Answer approved for tokenization")
                        
                        # Step 4: Mint NES Token
                        self.logger.info("Step 4: Minting NES token...")
                        mint_result = self.ledger.mint_nes_token(
                            answer_id=answer.id,
                            question=question.question,
                            answer=answer.answer,
                            evaluation_scores=asdict(evaluation_scores),
                            answer_metadata={
                                "sources": answer.sources,
                                "equations": answer.equations,
                                "examples": answer.examples,
                                "citations": answer.citations,
                                "model_version": answer.model_version
                            }
                        )
                        
                        cycle_report["tokens_minted"].append({
                            "answer_id": answer.id,
                            "tx_id": mint_result["tx_id"],
                            "status": mint_result["status"]
                        })
                        
                        self.execution_stats["total_tokens_minted"] += 1
                        
                        # Step 5: Update Knowledge Base
                        self.logger.info("Step 5: Updating knowledge base...")
                        self.ni_core.add_to_knowledge_base(answer)
                        
                    else:
                        self.logger.warning(
                            f"Answer rejected. Accuracy: {evaluation_scores.scientific_accuracy:.2f}, "
                            f"Novelty: {evaluation_scores.novelty_score:.2f}"
                        )
                        cycle_report["answers"][-1]["status"] = "rejected"
                    
                    self.execution_stats["total_answers_generated"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing question: {str(e)}"
                    self.logger.error(error_msg)
                    cycle_report["errors"].append(error_msg)
            
            # Step 6: Mine Block
            self.logger.info("Step 6: Mining block...")
            mined_block = self.ledger.mine_pending_block()
            
            if mined_block:
                cycle_report["mined_block"] = {
                    "block_number": mined_block.block_number,
                    "hash": mined_block.calculate_hash(),
                    "transactions_count": len(mined_block.transactions),
                    "timestamp": mined_block.timestamp
                }
            
            # Verify blockchain integrity
            self.logger.info("Verifying blockchain integrity...")
            integrity_ok = self.ledger.verify_chain_integrity()
            cycle_report["blockchain_integrity"] = integrity_ok
            
            # Update statistics
            cycle_end_time = datetime.now()
            cycle_duration = (cycle_end_time - cycle_start_time).total_seconds()
            
            cycle_report["end_time"] = cycle_end_time.isoformat()
            cycle_report["duration_seconds"] = cycle_duration
            cycle_report["status"] = "completed"
            
            self.execution_stats["successful_cycles"] += 1
            self.execution_stats["total_cycles"] += 1
            
            # Calculate average accuracy
            if cycle_report["evaluations"]:
                avg_accuracy = sum(
                    e["scientific_accuracy"] for e in cycle_report["evaluations"]
                ) / len(cycle_report["evaluations"])
                self.execution_stats["average_accuracy"] = avg_accuracy
            
            self.cycle_history.append(cycle_report)
            
            # Save cycle report to file
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            report_filename = reports_dir / f"cycle_report_{cycle_report["cycle_number"]}_{datetime.now().strftime("%Y%m%d%H%M%S")}.json"
            with open(report_filename, "w") as f:
                json.dump(cycle_report, f, indent=4)
            self.logger.info(f"Cycle report saved to {report_filename}")

            # Export blockchain ledger
            exports_dir = Path("exports")
            exports_dir.mkdir(exist_ok=True)
            ledger_filename = exports_dir / f"blockchain_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.json"
            with open(ledger_filename, "w") as f:
                json.dump(self.ledger.export_ledger(), f, indent=4)
            self.logger.info(f"Blockchain ledger exported to {ledger_filename}")
            self.cycle_count += 1
            
            self.logger.info(f"Operation cycle #{self.cycle_count} completed successfully")
            
        except Exception as e:
            error_msg = f"Critical error in operation cycle: {str(e)}"
            self.logger.error(error_msg)
            cycle_report["status"] = "failed"
            cycle_report["errors"].append(error_msg)
            self.execution_stats["failed_cycles"] += 1
            self.execution_stats["total_cycles"] += 1
        
        return cycle_report
    
    async def run_continuous(self, max_cycles: Optional[int] = None) -> None:
        """
        Run the operation loop continuously.
        
        Args:
            max_cycles: Maximum number of cycles to run (None for infinite)
        """
        self.logger.info(f"Starting continuous operation loop (interval: {self.config.interval_minutes} min)")
        
        cycle_count = 0
        while max_cycles is None or cycle_count < max_cycles:
            try:
                # Execute one cycle
                cycle_report = await self.execute_cycle()
                
                # Log cycle report
                self.logger.info(f"Cycle report: {json.dumps(cycle_report, indent=2)}")
                
                # Wait before next cycle
                wait_seconds = self.config.interval_minutes * 60
                self.logger.info(f"Waiting {self.config.interval_minutes} minutes until next cycle...")
                await asyncio.sleep(wait_seconds)
                
                cycle_count += 1
                
            except Exception as e:
                self.logger.error(f"Error in continuous loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get current execution statistics."""
        return {
            **self.execution_stats,
            "cycles_history": self.cycle_history[-10:] if self.cycle_history else [],
            "last_cycle_time": self.cycle_history[-1]["end_time"] if self.cycle_history else None,
            "ledger_state": self.ledger.get_chain_state()
        }
    
    def generate_cycle_report(self, cycle_report: Dict[str, Any]) -> str:
        """Generate a human-readable report for a cycle."""
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    NUCLEAR INTELLIGENCE OPERATION CYCLE REPORT                ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Cycle Number: {cycle_report['cycle_number']}
Status: {cycle_report['status'].upper()}
Duration: {cycle_report.get('duration_seconds', 'N/A')} seconds
Start Time: {cycle_report['start_time']}
End Time: {cycle_report.get('end_time', 'In Progress')}

─────────────────────────────────────────────────────────────────────────────────
QUESTIONS GENERATED: {len(cycle_report['questions'])}
─────────────────────────────────────────────────────────────────────────────────
"""
        for q in cycle_report['questions']:
            report += f"""
Question ID: {q['id']}
Category: {q['category']}
Complexity: {q['complexity']}/10
Question: {q['question'][:150]}...
Keywords: {', '.join(q['keywords'][:3])}
"""
        
        report += f"""
─────────────────────────────────────────────────────────────────────────────────
ANSWERS GENERATED: {len(cycle_report['answers'])}
─────────────────────────────────────────────────────────────────────────────────
"""
        for a in cycle_report['answers']:
            report += f"""
Answer ID: {a['id']}
Status: {a.get('status', 'processed')}
Sources: {a['sources_count']}
Equations: {a['equations_count']}
"""
        
        report += f"""
─────────────────────────────────────────────────────────────────────────────────
EVALUATIONS: {len(cycle_report['evaluations'])}
─────────────────────────────────────────────────────────────────────────────────
"""
        for e in cycle_report['evaluations']:
            report += f"""
Answer: {e['answer_id']}
Scientific Accuracy: {e['scientific_accuracy']:.2f}%
Novelty Score: {e['novelty_score']:.2f}%
Usefulness Score: {e['usefulness_score']:.2f}%
Self-Consistency: {e['self_consistency']:.2f}%
Overall Score: {e['overall_score']:.2f}%
"""
        
        report += f"""
─────────────────────────────────────────────────────────────────────────────────
NES TOKENS MINTED: {len(cycle_report['tokens_minted'])}
─────────────────────────────────────────────────────────────────────────────────
"""
        for t in cycle_report['tokens_minted']:
            report += f"""
Answer: {t['answer_id']}
Transaction ID: {t['tx_id']}
Status: {t['status']}
"""
        
        if 'mined_block' in cycle_report:
            mb = cycle_report['mined_block']
            report += f"""
─────────────────────────────────────────────────────────────────────────────────
BLOCKCHAIN STATE
─────────────────────────────────────────────────────────────────────────────────
Block Number: {mb['block_number']}
Block Hash: {mb['hash'][:16]}...
Transactions in Block: {mb['transactions_count']}
Blockchain Integrity: {'✓ VERIFIED' if cycle_report.get('blockchain_integrity') else '✗ FAILED'}
"""
        
        if cycle_report['errors']:
            report += f"""
─────────────────────────────────────────────────────────────────────────────────
ERRORS: {len(cycle_report['errors'])}
─────────────────────────────────────────────────────────────────────────────────
"""
            for error in cycle_report['errors']:
                report += f"• {error}\n"
        
        report += """
═════════════════════════════════════════════════════════════════════════════════
"""
        return report
