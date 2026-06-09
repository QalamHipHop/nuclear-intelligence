"""
Enhanced Operation Loop for Autonomous Nuclear Intelligence Research Cycle.
Orchestrates question generation, deep research, evaluation, and token minting.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from nuclear_intelligence_enhanced import (
    NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
)
from blockchain.enhanced_virtual_ledger import EnhancedVirtualLedger, TransactionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedOperationLoop:
    """Enhanced Operation Loop for autonomous research cycle."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logger
        
        # Initialize NI Core
        self.ni_core = NuclearIntelligenceCore(config)
        
        # Initialize Virtual Ledger
        self.ledger = EnhancedVirtualLedger(config)
        
        # Configuration thresholds
        self.scientific_accuracy_threshold = config.get("scientific_accuracy_threshold", 93)
        self.novelty_threshold = config.get("novelty_threshold", 75)
        self.usefulness_threshold = config.get("usefulness_threshold", 80)
        self.self_consistency_threshold = config.get("self_consistency_threshold", 90)
        self.overall_score_threshold = config.get("overall_score_threshold", 85)
        
        # Cycle tracking
        self.cycle_count = 0
        self.successful_mints = 0
        self.failed_evaluations = 0
    
    async def execute_research_cycle(self) -> Dict[str, Any]:
        """Execute a complete research cycle."""
        self.cycle_count += 1
        cycle_start_time = datetime.now()
        
        self.logger.info(f"Starting Research Cycle #{self.cycle_count}")
        
        cycle_results = {
            "cycle_number": self.cycle_count,
            "start_time": cycle_start_time.isoformat(),
            "questions_generated": 0,
            "answers_generated": 0,
            "answers_evaluated": 0,
            "tokens_minted": 0,
            "failed_evaluations": 0,
            "details": []
        }
        
        try:
            # Step 1: Generate Complex Questions
            self.logger.info("Step 1: Generating complex research questions...")
            questions = await self.ni_core.generate_complex_questions(num_questions=3)
            cycle_results["questions_generated"] = len(questions)
            
            # Step 2-4: Research, Evaluate, and Mint for each question
            for question in questions:
                question_result = {
                    "question_id": question.id,
                    "question": question.question[:100],
                    "category": question.category.value,
                    "status": "pending"
                }
                
                try:
                    # Step 2: Conduct Deep Research
                    self.logger.info(f"Step 2: Conducting deep research for question {question.id}...")
                    answer = await self.ni_core.conduct_deep_research(question)
                    cycle_results["answers_generated"] += 1
                    question_result["answer_id"] = answer.id
                    
                    # Step 3: Multi-layer Evaluation
                    self.logger.info(f"Step 3: Evaluating answer {answer.id}...")
                    evaluation_scores = await self.ni_core.evaluate_answer(answer)
                    answer.evaluation_scores = evaluation_scores
                    cycle_results["answers_evaluated"] += 1
                    
                    # Check evaluation thresholds
                    if self._meets_evaluation_criteria(evaluation_scores):
                        # Step 4: Mint NES Token
                        self.logger.info(f"Step 4: Minting NES token for answer {answer.id}...")
                        mint_result = self.ledger.mint_nes_token(
                            answer_id=answer.id,
                            question=question.question,
                            answer=answer.answer,
                            evaluation_scores=asdict(evaluation_scores),
                            answer_metadata={
                                "model_version": answer.model_version,
                                "category": question.category.value,
                                "complexity_level": question.complexity_level,
                                "sources_count": len(answer.sources),
                                "equations_count": len(answer.equations),
                                "citations_count": len(answer.citations)
                            }
                        )
                        
                        cycle_results["tokens_minted"] += 1
                        question_result["status"] = "token_minted"
                        question_result["mint_result"] = mint_result
                        
                        # Step 5: Add to Knowledge Base
                        self.logger.info(f"Step 5: Adding answer to knowledge base...")
                        self.ni_core.add_to_knowledge_base(answer)
                        
                        self.successful_mints += 1
                    else:
                        self.logger.warning(f"Answer {answer.id} did not meet evaluation criteria.")
                        question_result["status"] = "evaluation_failed"
                        question_result["evaluation_scores"] = asdict(evaluation_scores)
                        cycle_results["failed_evaluations"] += 1
                        self.failed_evaluations += 1
                
                except Exception as e:
                    self.logger.error(f"Error processing question {question.id}: {e}")
                    question_result["status"] = "error"
                    question_result["error"] = str(e)
                
                cycle_results["details"].append(question_result)
            
            # Mine pending block
            self.logger.info("Mining pending block...")
            mined_block = self.ledger.mine_pending_block()
            if mined_block:
                cycle_results["block_mined"] = {
                    "block_number": mined_block.block_number,
                    "block_hash": mined_block.calculate_hash(),
                    "transactions_count": len(mined_block.transactions)
                }
            
            # Get chain state
            chain_state = self.ledger.get_chain_state()
            cycle_results["chain_state"] = chain_state
            
            # Get knowledge summary
            knowledge_summary = self.ni_core.get_knowledge_summary()
            cycle_results["knowledge_summary"] = knowledge_summary
            
        except Exception as e:
            self.logger.error(f"Critical error in research cycle: {e}")
            cycle_results["error"] = str(e)
        
        cycle_end_time = datetime.now()
        cycle_results["end_time"] = cycle_end_time.isoformat()
        cycle_results["duration_seconds"] = (cycle_end_time - cycle_start_time).total_seconds()
        
        self.logger.info(f"Research Cycle #{self.cycle_count} completed.")
        
        return cycle_results
    
    def _meets_evaluation_criteria(self, scores: EvaluationScore) -> bool:
        """Check if evaluation scores meet the acceptance criteria."""
        return (
            scores.scientific_accuracy >= self.scientific_accuracy_threshold and
            scores.novelty_score >= self.novelty_threshold and
            scores.usefulness_score >= self.usefulness_threshold and
            scores.self_consistency >= self.self_consistency_threshold and
            scores.overall_score >= self.overall_score_threshold
        )
    
    async def run_continuous_loop(self, interval_minutes: int = 30):
        """Run the operation loop continuously at specified intervals."""
        self.logger.info(f"Starting continuous operation loop (interval: {interval_minutes} minutes)...")
        
        while True:
            try:
                cycle_result = await self.execute_research_cycle()
                
                # Log cycle result
                self.logger.info(f"Cycle Result: {json.dumps(cycle_result, indent=2)}")
                
                # Wait for next cycle
                self.logger.info(f"Waiting {interval_minutes} minutes until next cycle...")
                await asyncio.sleep(interval_minutes * 60)
            
            except KeyboardInterrupt:
                self.logger.info("Continuous loop interrupted by user.")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get statistics about the operation loop."""
        return {
            "total_cycles": self.cycle_count,
            "successful_mints": self.successful_mints,
            "failed_evaluations": self.failed_evaluations,
            "success_rate": (
                self.successful_mints / (self.successful_mints + self.failed_evaluations)
                if (self.successful_mints + self.failed_evaluations) > 0
                else 0
            ),
            "chain_state": self.ledger.get_chain_state(),
            "knowledge_summary": self.ni_core.get_knowledge_summary()
        }


# ==================== Main Execution ====================

async def main():
    """Main execution function."""
    config = {
        "llm_model": "gpt-4-turbo",
        "openai_api_key": "your-api-key",
        "blockchain_secret": "nuclear-intelligence-secret",
        "scientific_accuracy_threshold": 93,
        "novelty_threshold": 75,
        "usefulness_threshold": 80,
        "self_consistency_threshold": 90,
        "overall_score_threshold": 85
    }
    
    operation_loop = EnhancedOperationLoop(config)
    
    # Execute a single cycle for testing
    cycle_result = await operation_loop.execute_research_cycle()
    print("\nCycle Result:")
    print(json.dumps(cycle_result, indent=2))
    
    # Get statistics
    stats = operation_loop.get_operation_statistics()
    print("\nOperation Statistics:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
