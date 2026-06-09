
import time
import logging
from typing import Dict, Any

from pydantic import BaseModel, Field

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from blockchain.virtual_ledger import VirtualLedger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class OperationLoopConfig(BaseModel):
    question_generation_context: str = Field(default="", description="Context for generating research questions.")
    min_scientific_accuracy: float = Field(default=93.0, description="Minimum scientific accuracy score for token minting.")
    loop_interval_seconds: int = Field(default=1800, description="Interval between operation cycles in seconds (30 minutes).")

class OperationLoop:
    def __init__(
        self,
        nuclear_intelligence_core: NuclearIntelligenceCore,
        virtual_ledger: VirtualLedger,
        config: OperationLoopConfig
    ):
        self.ni_core = nuclear_intelligence_core
        self.virtual_ledger = virtual_ledger
        self.config = config

    def run_single_cycle(self):
        logging.info("Starting a new operation cycle...")
        try:
            # Step 1: Question Generation
            question = self.ni_core.generate_question(context=self.config.question_generation_context)
            logging.info(f"Generated Question: {question.question}")

            # Step 2: Deep Research
            answer = self.ni_core.conduct_research(question)
            logging.info(f"Research Answer (excerpt): {answer.answer[:100]}...")

            # Step 3: Multi-layer Professional Evaluation
            evaluation = self.ni_core.evaluate_answer(question, answer)
            logging.info(f"Evaluation: Accuracy={evaluation.scientific_accuracy}, Novelty={evaluation.novelty_score}, Usefulness={evaluation.usefulness_score}")

            # Step 4: Token Minting (if approved)
            if evaluation.scientific_accuracy >= self.config.min_scientific_accuracy and evaluation.self_consistency_check:
                logging.info("Answer approved for token minting.")
                # Add knowledge to NI Core's knowledge base
                self.ni_core.add_knowledge(question, answer, evaluation)

                # Mint NES token
                token_metadata = {
                    "question": question.dict(),
                    "answer": answer.dict(),
                    "evaluation": evaluation.dict(),
                    "timestamp": datetime.now().isoformat(),
                    "model_version": self.ni_core.llm.model_name, # Assuming llm has model_name attribute
                    "huggingface_link": "#TODO: Add Hugging Face Space link here"
                }
                self.virtual_ledger.mint_nes_token(token_metadata)
                logging.info("NES token minted and knowledge integrated.")
            else:
                logging.warning(f"Answer not approved for token minting. Accuracy: {evaluation.scientific_accuracy} (Min: {self.config.min_scientific_accuracy}), Self-consistency: {evaluation.self_consistency_check}")

            logging.info("Operation cycle completed successfully.")

        except Exception as e:
            logging.error(f"Error during operation cycle: {e}", exc_info=True)

    def start_loop(self):
        logging.info(f"Starting operation loop with interval: {self.config.loop_interval_seconds} seconds.")
        while True:
            self.run_single_cycle()
            logging.info(f"Waiting for {self.config.loop_interval_seconds} seconds before next cycle...")
            time.sleep(self.config.loop_interval_seconds)

if __name__ == "__main__":
    # Example Usage (requires VirtualLedger to be properly set up)
    # This part is for local testing and demonstration
    from blockchain.virtual_ledger import VirtualLedger, Block, Transaction

    # Initialize NI Core and Virtual Ledger
    ni_core_instance = NuclearIntelligenceCore()
    virtual_ledger_instance = VirtualLedger()

    # Configure the operation loop
    op_config = OperationLoopConfig(
        question_generation_context="Focus on advanced nuclear reactor designs and their economic implications.",
        min_scientific_accuracy=90.0, # Lower for testing
        loop_interval_seconds=10 # Shorter for testing
    )

    # Create and start the operation loop
    op_loop = OperationLoop(ni_core_instance, virtual_ledger_instance, op_config)
    # op_loop.start_loop() # Uncomment to run continuously
    op_loop.run_single_cycle() # Run a single cycle for demonstration


