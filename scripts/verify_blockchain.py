#!/usr/bin/env python3
"""
Verify blockchain integrity and consistency.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from blockchain.virtual_ledger import VirtualLedger


def main():
    """Verify blockchain integrity."""
    logger.info("Starting blockchain verification...")
    
    config = {
        "blockchain_secret": "nuclear-intelligence-secret"
    }
    
    ledger = VirtualLedger(config)
    
    # Verify chain integrity
    is_valid = ledger.verify_chain_integrity()
    
    # Get chain state
    chain_state = ledger.get_chain_state()
    
    logger.info(f"Blockchain Integrity: {'✓ VALID' if is_valid else '✗ INVALID'}")
    logger.info(f"Chain length: {chain_state['chain_length']}")
    logger.info(f"Pending transactions: {chain_state['pending_transactions']}")
    logger.info(f"Total NES minted: {chain_state['total_nes_minted']}")
    
    if not is_valid:
        logger.error("Blockchain integrity check failed!")
        return 1
    
    logger.info("Blockchain verification completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
