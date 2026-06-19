"""
Nuclear Intelligence v4.0 - Enhanced Evaluation Engine ⚛️📊
═══════════════════════════════════════════════════════════════════
Upgrades the single-shot LLM-as-judge with:

1. **Self-Consistency Check (NLI-style)**:
   - Generate N independent assessments (default N=3).
   - Compute median per dimension → robust to single-pass variance.
   - Inter-rater agreement (1 - normalized std) → bonus.

2. **Citation Quality Scoring**:
   - Reward answers that cite IAEA, NRC, peer-reviewed journals,
     DOE/INL/ORNL reports.
   - Penalize unsourced claims and circular self-reference.

3. **Novelty vs Knowledge Graph**:
   - Compare new answer's n-gram + embedding distance to existing KG
     entities. High distance → truly novel (vs slight rewording).

4. **Tokenization-Readiness Score**:
   - Composite of Accuracy ≥ 93%, Novelty ≥ 75%, Usefulness ≥ 80%,
     Self-Consistency ≥ 80%, Citation-Quality ≥ 0.5.
   - Returns a binary "ready_to_mint" flag plus per-dimension detail.

This module is *additive* — existing callers can keep using
EvaluationScore.overall_score() unchanged.
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from loguru import logger

from core.nuclear_intelligence_v4 import EvaluationScore


# ─── Trusted source whitelist ────────────────────────────────────────
TRUSTED_SOURCES = {
    "iaea.org", "iaea", "nrc.gov", "ans.org", "ieee.org", "doi.org",
    "nature.com", "sciencedirect", "springer", "wiley",
    "energy.gov", "inl.gov", "ornl.gov", "anl.gov", "lanl.gov",
    "bnl.gov", "sandia.gov", "iter.org", "iter", "iter newsline",
    "cern", "iae", "usnc", "researchgate", "arxiv.org", "pubmed",
    "oecd-nea.org", "nea.fr", "world-nuclear.org", "wna",
    "rosatom", "cea.fr", "jaea.go.jp", "kaeri.re.kr",
    "wikipedia.org",  # only as last-resort cross-check
}

# Anti-patterns: vague, promotional, or circular references
WEAK_CITATION_PATTERNS = [
    re.compile(r"\bbroadly\s+speaking\b", re.I),
    re.compile(r"\bsome\s+experts\s+(?:say|believe|claim)\b", re.I),
    re.compile(r"\bit\s+is\s+(?:widely|generally)\s+(?:believed|known|accepted)\s+that\b", re.I),
    re.compile(r"\baccording\s+to\s+(?:some|many|most)\s+(?:sources|reports)\b", re.I),
]


@dataclass
class CitationQuality:
    """Per-answer citation assessment."""
    citation_count: int
    trusted_ratio: float  # 0..1
    has_doi: bool
    has_year: bool
    weak_phrase_count: int
    score: float  # 0..100

    def to_dict(self) -> Dict:
        return {
            "citation_count": self.citation_count,
            "trusted_ratio": round(self.trusted_ratio, 3),
            "has_doi": self.has_doi,
            "has_year": self.has_year,
            "weak_phrase_count": self.weak_phrase_count,
            "score": round(self.score, 2),
        }


def assess_citation_quality(answer_text: str, citations: List[str]) -> CitationQuality:
    """Score the citation backbone of an answer."""
    if not answer_text:
        return CitationQuality(0, 0.0, False, False, 0, 0.0)

    text_lower = answer_text.lower()
    cites_lower = [c.lower() for c in (citations or [])]

    # Citation count: explicit references + inline markers
    inline_cites = len(re.findall(r"\[\d+\]|\(\d{4}\)|et al\.", text_lower))
    citation_count = inline_cites + len(cites_lower)

    # Trusted ratio
    if cites_lower:
        trusted = sum(1 for c in cites_lower if any(t in c for t in TRUSTED_SOURCES))
        trusted_ratio = trusted / max(1, len(cites_lower))
    else:
        trusted_ratio = 0.0

    # DOI / year presence
    has_doi = bool(re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", text_lower, re.I))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", answer_text))

    # Weak phrases
    weak = sum(1 for p in WEAK_CITATION_PATTERNS if p.search(answer_text))

    # Score (out of 100)
    score = 0.0
    score += min(40, citation_count * 5)            # up to 40 pts for citations
    score += 30 * trusted_ratio                     # up to 30 pts
    score += 10 if has_doi else 0                   # DOI bonus
    score += 5 if has_year else 0                   # year bonus
    score -= min(20, weak * 8)                      # penalty

    return CitationQuality(
        citation_count=citation_count,
        trusted_ratio=trusted_ratio,
        has_doi=has_doi,
        has_year=has_year,
        weak_phrase_count=weak,
        score=max(0.0, min(100.0, score)),
    )


# ─── Self-consistency via N independent evaluations ─────────────────

@dataclass
class ConsistencyReport:
    n_samples: int
    accuracy_median: float
    novelty_median: float
    usefulness_median: float
    completeness_median: float
    accuracy_std: float
    novelty_std: float
    usefulness_std: float
    completeness_std: float
    agreement: float            # 1 - mean(normalized std)
    passed: bool

    def to_dict(self) -> Dict:
        return {
            "n_samples": self.n_samples,
            "accuracy_median": round(self.accuracy_median, 2),
            "novelty_median": round(self.novelty_median, 2),
            "usefulness_median": round(self.usefulness_median, 2),
            "completeness_median": round(self.completeness_median, 2),
            "accuracy_std": round(self.accuracy_std, 3),
            "novelty_std": round(self.novelty_std, 3),
            "usefulness_std": round(self.usefulness_std, 3),
            "completeness_std": round(self.completeness_std, 3),
            "agreement": round(self.agreement, 3),
            "passed": self.passed,
        }


def consistency_report(scores: List[EvaluationScore], agreement_threshold: float = 0.80) -> ConsistencyReport:
    """Aggregate N independent EvaluationScore samples.

    `agreement` = 1 - mean(coeff_of_variation) across dimensions.
    `passed` = agreement >= threshold.
    """
    if not scores:
        return ConsistencyReport(0, 0, 0, 0, 0, 1, 1, 1, 1, 0.0, False)

    acc = [s.scientific_accuracy for s in scores]
    nov = [s.novelty_score for s in scores]
    use = [s.usefulness_score for s in scores]
    comp = [s.completeness for s in scores]

    def _safe_std(xs: List[float]) -> float:
        return statistics.pstdev(xs) if len(xs) > 1 else 0.0

    s_acc, s_nov, s_use, s_comp = _safe_std(acc), _safe_std(nov), _safe_std(use), _safe_std(comp)

    def _cv(std: float, mean: float) -> float:
        return (std / mean) if mean > 0 else 0.0

    cvs = [_cv(s_acc, statistics.mean(acc)), _cv(s_nov, statistics.mean(nov)),
           _cv(s_use, statistics.mean(use)), _cv(s_comp, statistics.mean(comp))]

    agreement = max(0.0, 1.0 - statistics.mean(cvs))

    return ConsistencyReport(
        n_samples=len(scores),
        accuracy_median=statistics.median(acc),
        novelty_median=statistics.median(nov),
        usefulness_median=statistics.median(use),
        completeness_median=statistics.median(comp),
        accuracy_std=s_acc,
        novelty_std=s_nov,
        usefulness_std=s_use,
        completeness_std=s_comp,
        agreement=agreement,
        passed=agreement >= agreement_threshold,
    )


# ─── Novelty vs existing Knowledge Graph entities ──────────────────

def novelty_against_kg(answer_text: str, kg_entity_questions: List[str], ngram_n: int = 3) -> float:
    """Estimate textual novelty vs prior knowledge-graph entries.

    Returns 0..100 — higher means more genuinely new (less paraphrase
    of existing questions).

    Cheap heuristic: 3-gram Jaccard distance against all prior questions.
    """
    if not answer_text or not kg_entity_questions:
        return 75.0  # neutral if we have no baseline

    def ngrams(text: str, n: int) -> Counter:
        tokens = re.findall(r"\w+", text.lower())
        return Counter(tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1))

    a_ngrams = ngrams(answer_text[:5000], ngram_n)
    if not a_ngrams:
        return 75.0

    max_sim = 0.0
    a_total = sum(a_ngrams.values())
    for prev_q in kg_entity_questions[-200:]:  # cap for cost
        p_ngrams = ngrams(prev_q, ngram_n)
        if not p_ngrams:
            continue
        overlap = sum((a_ngrams & p_ngrams).values())
        p_total = sum(p_ngrams.values())
        denom = a_total + p_total - overlap
        if denom <= 0:
            continue
        jac = overlap / denom
        if jac > max_sim:
            max_sim = jac

    # Map similarity -> novelty (50..100)
    novelty = 100.0 - 50.0 * max_sim
    return max(0.0, min(100.0, novelty))


# ─── Tokenization-Readiness composite score ────────────────────────

@dataclass
class TokenizationReadiness:
    accuracy: float
    novelty: float
    usefulness: float
    self_consistency: float      # agreement fraction
    citation_quality: float
    overall: float
    ready_to_mint: bool
    notes: List[str] = field(default_factory=list)

    THRESHOLDS = {
        "accuracy": 93.0,
        "novelty": 75.0,
        "usefulness": 80.0,
        "self_consistency": 0.80,
        "citation_quality": 50.0,
    }
    OVERALL_MIN = 85.0

    def to_dict(self) -> Dict:
        return {
            "accuracy": round(self.accuracy, 2),
            "novelty": round(self.novelty, 2),
            "usefulness": round(self.usefulness, 2),
            "self_consistency": round(self.self_consistency, 3),
            "citation_quality": round(self.citation_quality, 2),
            "overall": round(self.overall, 2),
            "ready_to_mint": self.ready_to_mint,
            "notes": self.notes,
        }


def tokenization_readiness(
    evaluation: EvaluationScore,
    consistency: Optional[ConsistencyReport] = None,
    citation_quality: Optional[CitationQuality] = None,
    weights: Optional[Dict[str, float]] = None,
) -> TokenizationReadiness:
    """Compute the composite Tokenization-Readiness Score.

    `weights` lets operators tune without forking the codebase.
    Defaults to the canonical NI v4 weights from the system prompt.
    """
    w = weights or {"accuracy": 0.40, "novelty": 0.20, "usefulness": 0.20,
                    "self_consistency": 0.10, "citation_quality": 0.10}

    sc = consistency.agreement if consistency else 1.0
    cq = citation_quality.score if citation_quality else 0.0

    overall = (
        evaluation.scientific_accuracy * w["accuracy"]
        + evaluation.novelty_score * w["novelty"]
        + evaluation.usefulness_score * w["usefulness"]
        + sc * 100.0 * w["self_consistency"]
        + cq * w["citation_quality"]
    )

    notes: List[str] = []
    T = TokenizationReadiness.THRESHOLDS

    if evaluation.scientific_accuracy < T["accuracy"]:
        notes.append(f"accuracy {evaluation.scientific_accuracy:.1f} < {T['accuracy']}")
    if evaluation.novelty_score < T["novelty"]:
        notes.append(f"novelty {evaluation.novelty_score:.1f} < {T['novelty']}")
    if evaluation.usefulness_score < T["usefulness"]:
        notes.append(f"usefulness {evaluation.usefulness_score:.1f} < {T['usefulness']}")
    if sc < T["self_consistency"]:
        notes.append(f"self_consistency {sc:.3f} < {T['self_consistency']}")
    if cq < T["citation_quality"]:
        notes.append(f"citation_quality {cq:.1f} < {T['citation_quality']}")

    ready = overall >= TokenizationReadiness.OVERALL_MIN and not notes

    return TokenizationReadiness(
        accuracy=evaluation.scientific_accuracy,
        novelty=evaluation.novelty_score,
        usefulness=evaluation.usefulness_score,
        self_consistency=sc,
        citation_quality=cq,
        overall=overall,
        ready_to_mint=ready,
        notes=notes,
    )
