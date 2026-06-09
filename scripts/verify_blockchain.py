
#!/usr/bin/env python3
"""
Verify blockchain integrity and consistency.
"""

import sys
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from blockchain.virtual_ledger import VirtualLedger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    """Verify blockchain integrity."""
    logging.info("Starting blockchain verification...")
    
    try:
        ledger = VirtualLedger()
        
        # Verify chain integrity
        is_valid = ledger.is_chain_valid()
        
        status_msg = "✓ VALID" if is_valid else "✗ INVALID"
        logging.info(f"Blockchain Integrity: {status_msg}")
        logging.info(f"Chain length: {len(ledger.chain)}")
        logging.info(f"Pending transactions: {len(ledger.pending_transactions)}")
        logging.info(f"Total NES minted: {ledger.nes_supply}")
        
        if not is_valid:
            logging.error("Blockchain integrity check failed!")
            return 1
        
        logging.info("Blockchain verification completed successfully!")
        return 0
        
    except Exception as e:
        logging.error(f"Critical error during blockchain verification: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
