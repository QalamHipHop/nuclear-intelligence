"""
Nuclear Intelligence v5.0 - Advanced AI Research Engine
═══════════════════════════════════════════════════════════════════
Multi-model LLM, Advanced RAG, Knowledge Graph, Multi-Layer Evaluation.
Re-exports the v4 core (kept for backward compatibility) and also exposes
the unified interface used by the operation loop.

Free provider chain: HF Router → Groq → DeepSeek → Gemini → Together → Fireworks → AIMLAPI
═══════════════════════════════════════════════════════════════════
"""

# Re-export everything from v4 for backward compatibility
from core.nuclear_intelligence_v4 import (
    NuclearIntelligenceCore,
    ResearchQuestion,
    ResearchAnswer,
    EvaluationScore,
    SYSTEM_PROMPTS,
    NUCLEAR_CATEGORIES,
    FALLBACK_QUESTIONS,
)

__all__ = [
    "NuclearIntelligenceCore",
    "ResearchQuestion",
    "ResearchAnswer",
    "EvaluationScore",
    "SYSTEM_PROMPTS",
    "NUCLEAR_CATEGORIES",
    "FALLBACK_QUESTIONS",
]
