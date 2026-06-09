#!/usr/bin/env python3
"""
Export complete system state for backup and analysis.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from blockchain.virtual_ledger import VirtualLedger
from core.nuclear_intelligence import NuclearIntelligenceCore


def main():
    """Export system state."""
    logger.info("Exporting system state...")
    
    config = {
        "blockchain_secret": "nuclear-intelligence-secret",
        "llm_model_large": "gpt-4-turbo"
    }
    
    # Initialize components
    ni_core = NuclearIntelligenceCore(config)
    ledger = VirtualLedger(config)
    
    # Prepare export
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "blockchain": ledger.export_ledger(),
        "knowledge_base": {
            "summary": ni_core.get_knowledge_summary(),
            "total_entries": len(ni_core.knowledge_base)
        }
    }
    
    # Save to file
    export_dir = Path(__file__).parent.parent / "exports"
    export_dir.mkdir(exist_ok=True)
    
    export_file = export_dir / f"system_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_file, "w") as f:
        json.dump(export_data, f, indent=2)
    
    logger.info(f"System state exported to {export_file}")
    logger.info(f"Blockchain blocks: {len(export_data['blockchain']['chain'])}")
    logger.info(f"Knowledge base entries: {export_data['knowledge_base']['total_entries']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
