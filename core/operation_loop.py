
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel, Field

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from blockchain.virtual_ledger import VirtualLedger

class OperationLoopConfig(BaseModel):
    interval_minutes: int = Field(default=45, description="Minutes between cycles")
    min_accuracy: float = Field(default=93.0, description="Minimum accuracy for minting")
    auto_start: bool = Field(default=True)

class OperationCycleResult(BaseModel):
    timestamp: str
    question: ResearchQuestion
    answer: ResearchAnswer
    evaluation: EvaluationScore
    minted: bool
    tx_hash: Optional[str] = None

class OperationLoop:
    def __init__(
        self,
        core: NuclearIntelligenceCore,
        ledger: VirtualLedger,
        config: OperationLoopConfig = OperationLoopConfig()
    ):
        self.core = core
        self.ledger = ledger
        self.config = config
        self.history: List[OperationCycleResult] = []
        self.is_running = False

    def run_cycle(self) -> OperationCycleResult:
        logger.info("--- Starting Nuclear Intelligence Operation Cycle ---")
        start_time = datetime.now()
        
        try:
            # 1. Question Generation
            logger.info("Step 1: Generating research question...")
            question = self.core.generate_question()
            logger.info(f"Question: {question.question}")

            # 2. Deep Research
            logger.info("Step 2: Conducting deep research...")
            answer = self.core.conduct_research(question)
            logger.info(f"Research complete. Length: {len(answer.answer)} chars")

            # 3. Evaluation
            logger.info("Step 3: Evaluating research output...")
            evaluation = self.core.evaluate_answer(question, answer)
            logger.info(f"Scores: Accuracy={evaluation.scientific_accuracy}, Novelty={evaluation.novelty_score}")

            # 4. Integration & Minting
            minted = False
            tx_hash = None
            if evaluation.scientific_accuracy >= self.config.min_accuracy and evaluation.self_consistency_check:
                logger.info("Step 4: Answer approved. Integrating knowledge and minting NES...")
                self.core.integrate_knowledge(question, answer, evaluation)
                
                metadata = {
                    "question": question.model_dump(),
                    "evaluation": evaluation.model_dump(),
                    "summary": answer.answer[:500]
                }
                self.ledger.mint_nes_token(metadata)
                tx_hash = self.ledger.get_last_block().hash
                minted = True
            else:
                logger.warning(f"Step 4: Answer rejected. Accuracy {evaluation.scientific_accuracy} < {self.config.min_accuracy}")

            result = OperationCycleResult(
                timestamp=start_time.isoformat(),
                question=question,
                answer=answer,
                evaluation=evaluation,
                minted=minted,
                tx_hash=tx_hash
            )
            self.history.append(result)
            self._save_report(result)
            
            logger.info(f"Cycle completed in {datetime.now() - start_time}")
            return result

        except Exception as e:
            logger.error(f"Cycle failed: {e}")
            raise

    def _save_report(self, result: OperationCycleResult):
        report_dir = "reports"
        os.makedirs(report_dir, exist_ok=True)
        filename = f"{report_dir}/cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=4))

    def start(self):
        self.is_running = True
        logger.info(f"Operation loop started. Interval: {self.config.interval_minutes} minutes")
        while self.is_running:
            try:
                self.run_cycle()
            except Exception as e:
                logger.error(f"Error in loop: {e}")
            
            logger.info(f"Waiting {self.config.interval_minutes} minutes...")
            time.sleep(self.config.interval_minutes * 60)

    def stop(self):
        self.is_running = False
        logger.info("Operation loop stopped.")
