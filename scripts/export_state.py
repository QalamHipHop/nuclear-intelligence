
#!/usr/bin/env python3
"""
Export complete system state for backup and analysis.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nuclear_intelligence import NuclearIntelligenceCore
from blockchain.virtual_ledger import VirtualLedger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def main():
    """Export system state."""
    logging.info("Exporting system state...")
    
    try:
        # Initialize components
        ni_core = NuclearIntelligenceCore()
        ledger = VirtualLedger()
        
        # Prepare export
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "blockchain_state": {
                "chain": [block.to_dict() for block in ledger.chain],
                "pending_transactions": [tx.to_dict() for tx in ledger.pending_transactions],
                "nes_supply": ledger.nes_supply
            },
            "knowledge_graph_state": ni_core.knowledge_graph.graph
        }
        
        # Save to file
        export_dir = Path(__file__).parent.parent / "exports"
        export_dir.mkdir(exist_ok=True)
        
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = export_dir / f"system_state_{ts}.json"
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"System state exported to {export_file}")
        blocks_count = len(export_data["blockchain_state"]["chain"])
        kg_entities_count = sum(len(v) for v in export_data["knowledge_graph_state"].values())
        logging.info(f"Blockchain blocks: {blocks_count}")
        logging.info(f"Knowledge graph entities: {kg_entities_count}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Critical error during state export: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
