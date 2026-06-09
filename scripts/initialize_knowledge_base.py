"""
Knowledge Base Initialization Script
Loads initial nuclear energy domain knowledge from various sources.
"""

import os
import json
from typing import List, Dict, Any
from loguru import logger

# Sample nuclear energy knowledge base
NUCLEAR_KNOWLEDGE_BASE = {
    "nuclear_physics": {
        "fission": {
            "description": "Nuclear fission is a reaction in which the nucleus of an atom splits into two or more smaller nuclei.",
            "key_concepts": [
                "Chain reaction",
                "Critical mass",
                "Neutron multiplication factor",
                "Prompt neutrons vs delayed neutrons"
            ],
            "applications": ["Nuclear power generation", "Nuclear weapons", "Medical isotopes"],
            "equations": [
                "E = mc²",
                "k_eff = (neutrons produced) / (neutrons absorbed or leaked)"
            ]
        },
        "fusion": {
            "description": "Nuclear fusion is a reaction in which two or more atomic nuclei combine to form one or more different atomic nuclei.",
            "key_concepts": [
                "Plasma confinement",
                "Coulomb barrier",
                "Reaction rate",
                "Triple product (nTτ)"
            ],
            "applications": ["Future power generation", "Hydrogen bombs", "Stellar processes"],
            "challenges": [
                "Achieving sustained fusion reaction",
                "Plasma instability",
                "Tritium breeding",
                "Materials damage"
            ]
        },
        "neutron_physics": {
            "description": "Study of neutron behavior in nuclear systems.",
            "topics": [
                "Neutron transport",
                "Cross-sections",
                "Moderation",
                "Absorption",
                "Scattering"
            ]
        }
    },
    "reactor_engineering": {
        "gen2_reactors": {
            "description": "Second generation reactors (1970s-1990s)",
            "types": ["PWR (Pressurized Water Reactor)", "BWR (Boiling Water Reactor)", "CANDU"],
            "characteristics": {
                "thermal_power": "1000-1500 MWth",
                "efficiency": "33-35%",
                "lifetime": "40 years (extended to 60-80)"
            }
        },
        "gen3_reactors": {
            "description": "Third generation reactors (1990s-present)",
            "types": ["AP1000", "EPR", "ESBWR", "ACR-1000"],
            "improvements": [
                "Enhanced safety systems",
                "Passive safety features",
                "Reduced construction time",
                "Higher efficiency (38-40%)"
            ]
        },
        "gen4_reactors": {
            "description": "Fourth generation reactors (future)",
            "types": [
                "Sodium-cooled fast reactors (SFR)",
                "Molten salt reactors (MSR)",
                "Very high temperature reactors (VHTR)",
                "Supercritical water reactors (SCWR)"
            ],
            "advantages": [
                "Improved safety",
                "Reduced waste",
                "Better fuel utilization",
                "Process heat applications"
            ]
        },
        "smr_microreactors": {
            "description": "Small Modular Reactors and Microreactors",
            "characteristics": {
                "power_output": "10-300 MWe",
                "applications": [
                    "Remote locations",
                    "Industrial heat",
                    "Desalination",
                    "Hydrogen production",
                    "District heating"
                ]
            }
        }
    },
    "safety_management": {
        "defense_in_depth": {
            "description": "Multi-layered safety approach",
            "levels": [
                "Prevention of abnormal operation",
                "Control of abnormal operation",
                "Mitigation of accident consequences",
                "Containment of radioactive material"
            ]
        },
        "waste_management": {
            "description": "Nuclear waste handling and disposal",
            "categories": [
                "Low-level waste (LLW)",
                "Intermediate-level waste (ILW)",
                "High-level waste (HLW)"
            ],
            "solutions": [
                "Deep geological repositories",
                "Transmutation",
                "Partitioning and transmutation (P&T)",
                "Interim storage"
            ]
        },
        "non_proliferation": {
            "description": "Preventing misuse of nuclear materials",
            "mechanisms": [
                "IAEA safeguards",
                "Export controls",
                "Fuel bank concepts",
                "Spent fuel repositories"
            ]
        }
    },
    "economics": {
        "lcoe": {
            "description": "Levelized Cost of Electricity",
            "components": [
                "Capital costs",
                "Operations & maintenance",
                "Fuel costs",
                "Decommissioning costs",
                "Financing costs"
            ],
            "nuclear_lcoe": "60-100 USD/MWh (depending on region and reactor type)"
        },
        "ppa_contracts": {
            "description": "Power Purchase Agreements",
            "types": [
                "Fixed-price PPA",
                "Escalating PPA",
                "Indexed PPA"
            ]
        },
        "tokenization": {
            "description": "Converting energy assets into blockchain tokens",
            "applications": [
                "Uranium tokenization",
                "Energy credit trading",
                "Fractional ownership",
                "Decentralized energy markets"
            ]
        }
    },
    "modern_applications": {
        "ai_data_centers": {
            "description": "Nuclear power for AI computing infrastructure",
            "advantages": [
                "High reliability for 24/7 operation",
                "Low carbon footprint",
                "Predictable costs",
                "On-site generation"
            ],
            "examples": ["Google-NuScale partnership", "Microsoft-SMR exploration"]
        },
        "desalination": {
            "description": "Using nuclear heat for water desalination",
            "technologies": [
                "Multi-effect distillation (MED)",
                "Reverse osmosis (RO)",
                "Thermal desalination"
            ]
        },
        "hydrogen_production": {
            "description": "Nuclear-powered hydrogen generation",
            "methods": [
                "Electrolysis with nuclear electricity",
                "Thermochemical water splitting",
                "High-temperature steam electrolysis"
            ]
        },
        "load_following": {
            "description": "Flexible nuclear power generation",
            "benefits": [
                "Grid stability",
                "Renewable integration",
                "Reduced curtailment",
                "Improved economics"
            ]
        }
    }
}


def initialize_knowledge_base() -> Dict[str, Any]:
    """Initialize the knowledge base with nuclear energy domain knowledge."""
    logger.info("Initializing Nuclear Intelligence knowledge base...")
    
    # Create knowledge base directory
    kb_dir = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")
    os.makedirs(kb_dir, exist_ok=True)
    
    # Save knowledge base as JSON
    kb_file = os.path.join(kb_dir, "nuclear_knowledge_base.json")
    with open(kb_file, "w", encoding="utf-8") as f:
        json.dump(NUCLEAR_KNOWLEDGE_BASE, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Knowledge base saved to {kb_file}")
    
    # Create index file
    index_file = os.path.join(kb_dir, "knowledge_index.json")
    index = {
        "categories": list(NUCLEAR_KNOWLEDGE_BASE.keys()),
        "total_entries": count_entries(NUCLEAR_KNOWLEDGE_BASE),
        "last_updated": __import__("datetime").datetime.now().isoformat(),
        "version": "0.1.0"
    }
    
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"Knowledge index saved to {index_file}")
    
    return index


def count_entries(data: Dict[str, Any]) -> int:
    """Count total entries in knowledge base."""
    count = 0
    for key, value in data.items():
        if isinstance(value, dict):
            count += 1 + count_entries(value)
        else:
            count += 1
    return count


def load_knowledge_base() -> Dict[str, Any]:
    """Load the knowledge base from file."""
    kb_file = os.path.join(
        os.path.dirname(__file__), "..", "knowledge_base", "nuclear_knowledge_base.json"
    )
    
    if os.path.exists(kb_file):
        with open(kb_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        logger.warning("Knowledge base file not found, initializing...")
        initialize_knowledge_base()
        return load_knowledge_base()


if __name__ == "__main__":
    logger.info("Starting knowledge base initialization...")
    index = initialize_knowledge_base()
    logger.info(f"Knowledge base initialized with {index['total_entries']} entries")
