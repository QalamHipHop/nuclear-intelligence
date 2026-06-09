
#!/usr/bin/env python3
"""
Run a single Nuclear Intelligence operation cycle.
This script executes one complete cycle of the operation loop.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

# Configure logging
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    logging.info("=" * 80)
    logging.info("NUCLEAR INTELLIGENCE OPERATION CYCLE")
    logging.info("=" * 80)
    logging.info(f"Start time: {datetime.now().isoformat()}")
    
    try:
        # Initialize core components
        logging.info("Initializing Nuclear Intelligence Core...")
        ni_core = NuclearIntelligenceCore()
        
        logging.info("Initializing Virtual Ledger...")
        virtual_ledger = VirtualLedger()

        # Configure the operation loop
        op_config = OperationLoopConfig(
            min_accuracy=float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", "93.0")),
            interval_minutes=int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", "30"))
        )
        
        logging.info("Initializing Operation Loop...")
        operation_loop = OperationLoop(ni_core, virtual_ledger, op_config)
        
        # Execute one cycle
        logging.info("Executing operation cycle...")
        operation_loop.run_cycle()
        
        logging.info("Operation cycle completed successfully.")
        logging.info(f"End time: {datetime.now().isoformat()}")
        logging.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logging.error(f"Critical error during operation cycle: {e}", exc_info=True)
        logging.error("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
