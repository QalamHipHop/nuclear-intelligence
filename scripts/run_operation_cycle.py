#!/usr/bin/env python3
"""
Run a single Nuclear Intelligence operation cycle.
This script executes one complete cycle of the operation loop.
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop
from blockchain.virtual_ledger import VirtualLedger


# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    log_dir / f"operation_cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)


def load_config() -> dict:
    """Load configuration from environment variables."""
    config = {
        "llm_model_large": os.getenv("LLM_MODEL_LARGE", "gpt-4-turbo"),
        "llm_model_medium": os.getenv("LLM_MODEL_MEDIUM", "gpt-3.5-turbo"),
        "scheduler_interval_minutes": int(os.getenv("SCHEDULER_INTERVAL_MINUTES", "45")),
        "min_accuracy_threshold": 93.0,
        "min_novelty_threshold": 70.0,
        "questions_per_cycle": int(os.getenv("QUESTIONS_PER_CYCLE", "3")),
        "feature_human_in_the_loop": os.getenv("FEATURE_HUMAN_IN_THE_LOOP", "true").lower() == "true",
        "blockchain_secret": os.getenv("BLOCKCHAIN_SECRET", "nuclear-intelligence-secret")
    }
    return config


async def main():
    """Main entry point."""
    logger.info("=" * 80)
    logger.info("NUCLEAR INTELLIGENCE OPERATION CYCLE")
    logger.info("=" * 80)
    logger.info(f"Start time: {datetime.now().isoformat()}")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded: {json.dumps(config, indent=2)}")
        
        # Initialize components
        logger.info("Initializing Nuclear Intelligence Core...")
        ni_core = NuclearIntelligenceCore(config)
        
        logger.info("Initializing Virtual Ledger...")
        virtual_ledger = VirtualLedger(config)
        
        logger.info("Initializing Operation Loop...")
        operation_loop = OperationLoop(ni_core, virtual_ledger, config)
        
        # Execute one cycle
        logger.info("Executing operation cycle...")
        cycle_report = await operation_loop.execute_cycle()
        
        # Generate human-readable report
        report_text = operation_loop.generate_cycle_report(cycle_report)
        logger.info(report_text)
        
        # Save report to file
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"cycle_{cycle_report['cycle_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(cycle_report, f, indent=2)
        
        logger.info(f"Cycle report saved to {report_file}")
        
        # Save blockchain state
        blockchain_export = virtual_ledger.export_ledger()
        blockchain_file = reports_dir / f"blockchain_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(blockchain_file, "w") as f:
            json.dump(blockchain_export, f, indent=2)
        
        logger.info(f"Blockchain state saved to {blockchain_file}")
        
        # Log final statistics
        logger.info("=" * 80)
        logger.info("OPERATION CYCLE STATISTICS")
        logger.info("=" * 80)
        stats = operation_loop.get_execution_stats()
        logger.info(f"Total cycles executed: {stats['total_cycles']}")
        logger.info(f"Successful cycles: {stats['successful_cycles']}")
        logger.info(f"Failed cycles: {stats['failed_cycles']}")
        logger.info(f"Total questions generated: {stats['total_questions_generated']}")
        logger.info(f"Total answers generated: {stats['total_answers_generated']}")
        logger.info(f"Total NES tokens minted: {stats['total_tokens_minted']}")
        logger.info(f"Average accuracy: {stats['average_accuracy']:.2f}%")
        logger.info("=" * 80)
        
        logger.info(f"End time: {datetime.now().isoformat()}")
        logger.info("Operation cycle completed successfully!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Critical error during operation cycle: {e}", exc_info=True)
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
