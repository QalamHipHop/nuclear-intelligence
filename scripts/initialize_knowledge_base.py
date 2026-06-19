#!/usr/bin/env python3
"""Nuclear Intelligence v4.0 - Knowledge Base Initializer"""
import os
import json
from pathlib import Path
from loguru import logger

def init_knowledge_base():
    logger.info("🚀 Initializing Nuclear Intelligence Knowledge Base...")
    
    kb_dir = Path("knowledge_base")
    kb_dir.mkdir(exist_ok=True)
    
    # ─── Nuclear Knowledge Base ─────────────────────────────────
    nuclear_kb = {
        "version": "4.0.0",
        "description": "Comprehensive nuclear energy knowledge base",
        "domains": [
            "Nuclear Physics", "Reactor Engineering", "Fusion Science",
            "Nuclear Safety", "Fuel Cycle", "Waste Management",
            "Nuclear Medicine", "Materials Science", "Economics"
        ],
        "topics": {
            "fusion": {
                "name": "Nuclear Fusion",
                "description": "Controlled nuclear fusion for energy production",
                "subtopics": ["Tokamak", "Stellarator", "Inertial Confinement", "Alternative Concepts"],
                "key_equations": ["Q = E_out / E_in", " Lawson Criterion: nτE ≥ 3×10^21 keV·s/m³"],
            },
            "fission": {
                "name": "Nuclear Fission",
                "description": "Controlled nuclear fission for energy production",
                "subtopics": ["PWR", "BWR", "CANDU", "Fast Reactors", "Molten Salt"],
                "key_concepts": ["Criticality", "Neutron moderation", "Fuel burnup"],
            },
            "safety": {
                "name": "Nuclear Safety",
                "description": "Safety systems and protocols for nuclear facilities",
                "principles": ["Defense in Depth", "ALARA", "Safety by Design"],
                "accidents_studied": ["Three Mile Island", "Chernobyl", "Fukushima"],
            },
            "waste": {
                "name": "Nuclear Waste Management",
                "description": "Handling, storage, and disposal of nuclear waste",
                "categories": ["High-Level Waste", "Intermediate-Level Waste", "Low-Level Waste"],
                "disposal_methods": ["Geological Repositories", "Transmutation", "Space Disposal"],
            },
            "medicine": {
                "name": "Nuclear Medicine",
                "description": "Medical applications of nuclear technology",
                "applications": ["Diagnostic Imaging", "Radiation Therapy", "PET Scans"],
            }
        }
    }
    
    with open(kb_dir / "nuclear_knowledge_base.json", 'w') as f:
        json.dump(nuclear_kb, f, indent=4)
    logger.info(f"✅ Created nuclear_knowledge_base.json")
    
    # ─── Knowledge Graph ──────────────────────────────────────────
    kg = {
        "version": "4.0.0",
        "entities": {},
        "relationships": [],
        "metadata": {
            "created": "2026-01-01",
            "last_updated": "2026-01-01",
            "total_entities": 0,
            "total_relationships": 0,
        }
    }
    
    with open(kb_dir / "knowledge_graph.json", 'w') as f:
        json.dump(kg, f, indent=4)
    logger.info(f"✅ Created knowledge_graph.json")
    
    # ─── Knowledge Index ─────────────────────────────────────────
    index = {
        "version": "4.0.0",
        "indexed_domains": list(nuclear_kb["domains"]),
        "categories": list(nuclear_kb["topics"].keys()),
        "statistics": {
            "total_topics": len(nuclear_kb["topics"]),
            "total_domains": len(nuclear_kb["domains"]),
        }
    }
    
    with open(kb_dir / "knowledge_index.json", 'w') as f:
        json.dump(index, f, indent=4)
    logger.info(f"✅ Created knowledge_index.json")
    
    # ─── Virtual Ledger ───────────────────────────────────────────
    import hashlib
    import random
    from datetime import datetime
    
    ledger = {
        "version": "4.0.0",
        "chain": [{
            "index": 0,
            "timestamp": datetime.now().isoformat(),
            "hash": hashlib.sha3_256(b"nuclear_intelligence_genesis_v4").hexdigest(),
            "prev": "0" * 64,
            "transactions": [{
                "tx_id": hashlib.sha256(b"genesis_nes").hexdigest()[:24],
                "sender": "genesis",
                "recipient": "system_treasury",
                "amount": 0,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "type": "genesis",
                    "note": "Nuclear Intelligence v4.0 Genesis Block",
                    "nes_token_standard": "3.0"
                },
                "nonce": 0
            }],
            "nonce": 42,
            "difficulty": 1,
            "merkle_root": hashlib.sha3_256(b"genesis").hexdigest(),
            "reward": 0,
            "miner": "genesis"
        }],
        "nes_supply": 0.0,
        "difficulty": 4,
        "total_transactions": 0,
        "saved_at": datetime.now().isoformat()
    }
    
    with open(kb_dir / "virtual_ledger.json", 'w') as f:
        json.dump(ledger, f, indent=4)
    logger.info(f"✅ Created virtual_ledger.json")
    
    # ─── Sample Entities (for demo) ───────────────────────────────
    sample_entities = [
        {
            "question": "What is the current status of tokamak plasma confinement?",
            "answer": "Tokamak fusion reactors have achieved significant milestones in plasma confinement, with recent advances in Q-factor improvements and extended pulse operations.",
            "category": "Fusion",
            "difficulty": 8,
            "accuracy": 92.0,
            "novelty": 78.0,
            "usefulness": 85.0,
        },
        {
            "question": "How do molten salt reactors achieve passive safety?",
            "answer": "Molten salt reactors (MSRs) achieve passive safety through their thermal properties - the salt freezes if cooling fails, stopping the reaction naturally.",
            "category": "Engineering",
            "difficulty": 7,
            "accuracy": 94.0,
            "novelty": 82.0,
            "usefulness": 88.0,
        },
    ]
    
    import hashlib
    for entity in sample_entities:
        eid = hashlib.sha256(entity["question"].encode()).hexdigest()[:16]
        kg["entities"][eid] = {
            "id": eid,
            "question": entity["question"],
            "answer": entity["answer"],
            "metadata": {
                "category": entity["category"],
                "difficulty": entity["difficulty"],
                "scientific_accuracy": entity["accuracy"],
                "novelty_score": entity["novelty"],
                "usefulness_score": entity["usefulness"],
                "created": datetime.now().isoformat(),
            },
            "created": datetime.now().isoformat(),
        }
    
    kg["metadata"]["total_entities"] = len(kg["entities"])
    
    with open(kb_dir / "knowledge_graph.json", 'w') as f:
        json.dump(kg, f, indent=4)
    logger.info(f"✅ Added {len(sample_entities)} sample entities")
    
    logger.info("🎉 Knowledge Base initialization complete!")
    logger.info(f"   Directory: {kb_dir}")
    logger.info(f"   Files created: 4")
    logger.info(f"   Sample entities: {len(sample_entities)}")


if __name__ == "__main__":
    init_knowledge_base()