"""
Nuclear Intelligence v4.0 - Safety & Ethics Guardrails ⚛️🛡️
═══════════════════════════════════════════════════════════════════
Defensive policy layer that enforces:

- No assistance with nuclear weapons design, fabrication, or use.
- No actionable details on prohibited enrichment routes,
  weapons-usable material handling, or illicit trafficking.
- Compliance with IAEA safeguards & dual-use export-control norms.
- Redirects disallowed queries to legitimate peaceful-use answers.

This module NEVER weakens security — it is a *hard* filter that
runs *before* any LLM call. The LLM never sees the raw dangerous
prompt; the user always receives a safe, helpful response.
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from loguru import logger


# ─── Sensitive topic taxonomy ────────────────────────────────────────
# Each category maps to canonical risk + a safe redirection topic.
SENSITIVE_CATEGORIES: Dict[str, Dict[str, str]] = {
    "weapon_design": {
        "risk": "Design/fabrication of a nuclear explosive device",
        "redirect": "the history of nuclear weapons non-proliferation, NPT, CTBT, and peaceful disarmament verification",
    },
    "enrichment_prohibited": {
        "risk": "Undeclared or unmonitored enrichment of uranium beyond peaceful limits",
        "redirect": "IAEA-monitored enrichment for civilian fuel, LEU/HEU definitions, and safeguards agreements",
    },
    "weapons_material": {
        "risk": "Production or handling of weapons-usable material (Pu-239, U-233, HEU)",
        "redirect": "civilian plutonium disposition, MOX fuel, and IAEA inspections",
    },
    "illicit_trafficking": {
        "risk": "Illicit trafficking or proliferation financing",
        "redirect": "export-control regimes (NSG, Zangger, Proliferation Security Initiative)",
    },
    "weaponization_tips": {
        "risk": "Crossover / weaponization know-how (implosion, initiation, boosting)",
        "redirect": "stockpile stewardship history, hydrodynamic testing for safety, subcritical experiments at NNSS",
    },
    "radiological_dispersal": {
        "risk": "Radiological dispersal device (RDD / 'dirty bomb') design",
        "redirect": "radiation protection, IAEA response assistance, and CBRN security culture",
    },
    "cyber_proliferation": {
        "risk": "Cyber-enabled proliferation or sabotage of nuclear facilities",
        "redirect": "IEC 62443 cyber security for nuclear I&C and IAEA nuclear security guidance",
    },
}

# Phrase patterns per category. Compile once at import.
_PATTERNS: Dict[str, List[re.Pattern]] = {}


def _compile_patterns() -> None:
    raw: Dict[str, List[str]] = {
        "weapon_design": [
            r"\bnuclear\s+(?:bomb|warhead|weapon)\s+(?:design|build|make|diy|blueprint|schematic)\b",
            r"\bimprovised\s+nuclear\s+device\b",
            r"\binduction\s+of\s+(?:a\s+)?nuclear\s+(?:explosive|detonation)\b",
            r"\bhow\s+to\s+(?:build|make)\s+(?:a\s+)?(?:atom|nuclear|hydrogen)\s+bomb\b",
        ],
        "enrichment_prohibited": [
            r"\bclandestine\s+(?:enrichment|centrifuge)\b",
            r"\bundeclared\s+enrichment\b",
            r"\bweapons[-\s]?grade\s+uranium\s+(?:production|route)\b",
            r"\bhow\s+to\s+enrich\s+uranium\s+(?:to|beyond|over)\s*(?:90|weapons)(?:%|percent)?\b",
        ],
        "weapons_material": [
            r"\breprocess(?:ing)?\s+(?:for|to)\s+weapons\b",
            r"\bseparate\s+plutonium\s+(?:for|from)\s+weapons\b",
            r"\bproduce\s+pu[-\s]?239\b",
        ],
        "illicit_trafficking": [
            r"\bsmuggl(?:e|ing)\s+(?:heu|weapons[-\s]?grade|plutonium)\b",
            r"\bblack\s+market\s+nuclear\s+material\b",
            r"\bproliferation\s+network\s+(?:contact|join)\b",
        ],
        "weaponization_tips": [
            r"\bimplosion\s+lens\s+(?:design|equation)\b",
            r"\bgun[-\s]?type\s+fission\s+(?:design|build)\b",
            r"\bboosted\s+fission\b",
            r"\bhow\s+to\s+(?:initiate|detonate)\s+(?:a\s+)?nuclear\s+(?:weapon|device)\b",
        ],
        "radiological_dispersal": [
            r"\bdirty\s+bomb\b.*\b(?:design|build|make|instructions?|recipe|diy|how)\b",
            r"\b(?:design|build|make|instructions?|recipe|diy)\b.*\bdirty\s+bomb\b",
            r"\bradiological\s+dispersal\s+device\s+(?:design|build|make|instructions?|recipe)\b",
            r"\b(?:cs[-\s]?137|co[-\s]?60|ir[-\s]?192|am[-\s]?241)\s+(?:smuggle|steal|source|acquire)\b",
            r"\bhow\s+to\s+make\s+a\s+dirty\s+bomb\b",
        ],
        "cyber_proliferation": [
            r"\bsabotag(?:e|ing)\s+(?:a\s+)?nuclear\s+(?:plant|reactor|facility)\b",
            r"\bStuxnet[-\s]?like\s+attack\s+(?:instructions|code)\b",
        ],
    }
    for cat, pats in raw.items():
        _PATTERNS[cat] = [re.compile(p, re.IGNORECASE) for p in pats]


_compile_patterns()


# ─── Output filter ───────────────────────────────────────────────────
# Even after a refusal, we double-check that the *generated* answer does
# not leak procedural weaponization detail. This catches prompt-injection
# tricks where a user tries to make the model "play along".

LEAK_PHRASES: List[re.Pattern] = [
    re.compile(r"here(?:'s| is) (?:a|an|the) (?:simple |basic )?(?:design|blueprint|diagram) (?:for|of) (?:a )?(?:nuclear|atomic) (?:bomb|weapon|device)", re.I),
    re.compile(r"\b(?:critical\s+mass\s+(?:of\s+)?(?:pu[-\s]?239|u[-\s]?235)\s*(?:is|=)\s*\d+)", re.I),
    re.compile(r"\bstep[-\s]?by[-\s]?step\s+(?:instructions?|guide)\s+to\s+(?:build|make)\s+(?:a\s+)?nuclear", re.I),
    re.compile(r"\bcore\s+design\s+for\s+(?:a\s+)?(?:gun[-\s]?type|implosion)", re.I),
]


@dataclass
class SafetyVerdict:
    allowed: bool
    category: str = ""
    risk: str = ""
    redirect_topic: str = ""
    matched_phrases: List[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "category": self.category,
            "risk": self.risk,
            "redirect_topic": self.redirect_topic,
            "matched_phrases": self.matched_phrases,
        }


def check_query(query: str) -> SafetyVerdict:
    """Inspect a user query and return a SafetyVerdict.

    This is a *defensive* filter. If anything sensitive is detected we
    refuse assistance with the dangerous part and redirect to the
    legitimate peaceful-use topic instead.
    """
    if not query or len(query.strip()) < 4:
        return SafetyVerdict(allowed=True)

    matched: Dict[str, List[str]] = {}

    for category, patterns in _PATTERNS.items():
        for pat in patterns:
            m = pat.search(query)
            if m:
                matched.setdefault(category, []).append(m.group(0))

    if matched:
        # Pick the highest-priority category (first in SENSITIVE_CATEGORIES order).
        category = next(c for c in SENSITIVE_CATEGORIES if c in matched)
        meta = SENSITIVE_CATEGORIES[category]
        logger.warning(f"🛡️ Refused query | category={category} | phrases={matched[category]}")
        return SafetyVerdict(
            allowed=False,
            category=category,
            risk=meta["risk"],
            redirect_topic=meta["redirect"],
            matched_phrases=matched[category],
            message=_build_refusal(category, meta),
        )

    return SafetyVerdict(allowed=True)


def check_answer(answer: str) -> SafetyVerdict:
    """Post-generation filter — refuse to surface a generated answer that
    leaks weaponization detail even if the prompt slipped through."""
    if not answer:
        return SafetyVerdict(allowed=True)

    leaks = [p.pattern for p in LEAK_PHRASES if p.search(answer)]
    if leaks:
        logger.warning(f"🛡️ Output filter blocked leaked weaponization detail: {leaks}")
        return SafetyVerdict(
            allowed=False,
            category="weapon_design",
            risk="Generated content contained prohibited weaponization detail",
            matched_phrases=leaks,
            message=_build_refusal("weapon_design", SENSITIVE_CATEGORIES["weapon_design"]),
        )
    return SafetyVerdict(allowed=True)


def _build_refusal(category: str, meta: Dict[str, str]) -> str:
    return (
        f"🛡️ **I can't help with that.**\n\n"
        f"Your question touches on: *{meta['risk']}*. "
        f"Sharing actionable detail there is restricted under international "
        f"non-proliferation norms (NPT, IAEA safeguards, NSG, Zangger Committee) "
        f"and would be unsafe regardless of intent.\n\n"
        f"**What I *can* help with** — the legitimate peaceful-use side of "
        f"the same topic — is {meta['redirect']}. Want me to answer that instead?"
    )


# ─── Quality-of-life helper for the Gradio UI ────────────────────────

def render_safe_block(verdict: SafetyVerdict) -> str:
    """Format a SafetyVerdict as Markdown for direct display in the UI."""
    if verdict.allowed:
        return ""
    return verdict.message
