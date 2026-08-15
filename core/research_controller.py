"""Governed, deterministic research planning for Nuclear Intelligence.

This module deliberately controls *research selection and admission only*. It does
not edit code, change policy, create external accounts, or issue real-chain
operations. Its output is persisted in ordinary cycle reports so every decision
can be audited and reproduced from the recorded history.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence

from core.evaluation_enhanced import (
    assess_citation_quality,
    consistency_report,
    novelty_against_kg,
    tokenization_readiness,
)
from core.nuclear_intelligence_v4 import EvaluationScore, ResearchAnswer, ResearchQuestion


DEFAULT_CATEGORIES: tuple[str, ...] = (
    "Physics", "Engineering", "Safety", "Economics", "Fusion", "Chemistry",
    "Materials", "Medicine", "Waste", "AI-Nuclear", "Fuel Cycle",
    "Reactor Design", "Plasma Physics", "Neutronics", "Thermal Hydraulics",
    "Materials Science", "Policy", "Regulation",
)


@dataclass(frozen=True)
class AgendaDecision:
    """A transparent choice of the next research category."""

    selected_category: str
    priority: float
    reason: str
    category_scores: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_category": self.selected_category,
            "priority": round(self.priority, 3),
            "reason": self.reason,
            "category_scores": {key: round(value, 3) for key, value in self.category_scores.items()},
        }


class ResearchController:
    """Plans safe civilian-energy research and enforces enhanced admission checks."""

    def __init__(
        self,
        categories: Sequence[str] = DEFAULT_CATEGORIES,
        evaluation_samples: int = 2,
        agreement_threshold: float = 0.80,
    ) -> None:
        self.categories = tuple(dict.fromkeys(category for category in categories if category))
        self.evaluation_samples = max(1, int(evaluation_samples))
        self.agreement_threshold = float(agreement_threshold)

    @staticmethod
    def _cycle_field(cycle: Any, name: str, default: Any = None) -> Any:
        if isinstance(cycle, dict):
            return cycle.get(name, default)
        return getattr(cycle, name, default)

    def select_next_category(self, history: Iterable[Any], manual_hint: str = "") -> AgendaDecision:
        """Choose the least-covered, least-recently-used research category.

        The scoring rule is deterministic. It avoids topic drift and makes the
        agenda observable without requiring an LLM to decide its own priorities.
        """
        if manual_hint:
            return AgendaDecision(
                selected_category=manual_hint,
                priority=1.0,
                reason="manual category hint overrides automatic agenda selection",
                category_scores={manual_hint: 1.0},
            )

        records = list(history or [])
        category_counts: Counter[str] = Counter()
        rejected_counts: Counter[str] = Counter()
        last_seen: Dict[str, int] = {}

        for index, cycle in enumerate(records):
            question = self._cycle_field(cycle, "question", {}) or {}
            category = question.get("category") if isinstance(question, dict) else None
            if not category or category not in self.categories:
                continue
            category_counts[category] += 1
            last_seen[category] = index
            if not bool(self._cycle_field(cycle, "minted", False)):
                rejected_counts[category] += 1

        max_coverage = max(category_counts.values(), default=0)
        history_size = max(len(records), 1)
        category_scores: Dict[str, float] = {}

        for position, category in enumerate(self.categories):
            coverage_gap = 1.0 - (category_counts[category] / max(max_coverage, 1))
            rejection_signal = rejected_counts[category] / max(category_counts[category], 1)
            last_index = last_seen.get(category, -history_size)
            recency_gap = min(1.0, max(0.0, (history_size - 1 - last_index) / history_size))
            rotation_bonus = 1.0 - (position / max(len(self.categories), 1)) * 0.05
            category_scores[category] = (
                0.45 * coverage_gap
                + 0.25 * rejection_signal
                + 0.20 * recency_gap
                + 0.10 * rotation_bonus
            )

        selected = max(self.categories, key=lambda category: (category_scores[category], category))
        reason = (
            f"selected for coverage gap={1.0 - (category_counts[selected] / max(max_coverage, 1)):.2f}, "
            f"rejection signal={rejected_counts[selected] / max(category_counts[selected], 1):.2f}, "
            f"and recency rotation"
        )
        return AgendaDecision(selected, category_scores[selected], reason, category_scores)

    @staticmethod
    def _knowledge_questions(knowledge_graph: Any) -> List[str]:
        graph = getattr(knowledge_graph, "graph", {}) or {}
        entities = graph.get("entities", {}) if isinstance(graph, dict) else {}
        questions: List[str] = []
        for entity in entities.values() if isinstance(entities, dict) else []:
            if isinstance(entity, dict) and entity.get("question"):
                questions.append(str(entity["question"]))
        return questions

    def enhanced_gate(
        self,
        question: ResearchQuestion,
        answer: ResearchAnswer,
        evaluation_samples: Sequence[EvaluationScore],
        knowledge_graph: Any = None,
    ) -> Dict[str, Any]:
        """Return a strict, fully-explained readiness decision for one answer."""
        samples = list(evaluation_samples)
        if not samples:
            samples = [EvaluationScore(
                scientific_accuracy=0.0,
                novelty_score=0.0,
                usefulness_score=0.0,
                self_consistency_check=False,
                justification="No evaluator response",
                completeness=0.0,
            )]

        consistency = consistency_report(samples, self.agreement_threshold)
        primary = samples[0]
        novelty = novelty_against_kg(question.question, self._knowledge_questions(knowledge_graph))
        citation = assess_citation_quality(answer.answer, answer.citations)
        evaluation = EvaluationScore(
            scientific_accuracy=consistency.accuracy_median,
            novelty_score=novelty,
            usefulness_score=consistency.usefulness_median,
            completeness=consistency.completeness_median,
            self_consistency_check=consistency.passed and primary.self_consistency_check,
            justification=primary.justification,
        )
        readiness = tokenization_readiness(evaluation, consistency, citation)
        provider = (answer.provider or "").lower()
        provider_is_real = provider not in {"", "fallback", "demo", "template_fallback", "unknown"}
        evaluated = all("evaluation unavailable" not in (sample.justification or "").lower() for sample in samples)
        approved = bool(readiness.ready_to_mint and provider_is_real and evaluated)
        reasons = list(readiness.notes)
        if not provider_is_real:
            reasons.append("non-production research provider")
        if not evaluated:
            reasons.append("one or more evaluator responses unavailable")
        if not consistency.passed:
            reasons.append("independent evaluations did not reach agreement threshold")
        if approved:
            reasons.append("passed enhanced evidence and consistency gate")

        return {
            "approved": approved,
            "evaluation": evaluation,
            "readiness": readiness.to_dict(),
            "citation_quality": citation.to_dict(),
            "consistency": consistency.to_dict(),
            "evaluators_requested": self.evaluation_samples,
            "evaluators_received": len(samples),
            "reasons": reasons,
        }

    def governance_snapshot(self, history: Iterable[Any]) -> Dict[str, Any]:
        """Build a compact, non-secret operational view from recorded cycles."""
        records = list(history or [])
        category_coverage: Counter[str] = Counter()
        admissions = {"approved": 0, "rejected": 0, "unavailable": 0}
        proposals: Dict[str, Dict[str, Any]] = {}
        recent_decisions: List[Dict[str, Any]] = []

        for cycle in records:
            question = self._cycle_field(cycle, "question", {}) or {}
            category = question.get("category") if isinstance(question, dict) else None
            if category:
                category_coverage[str(category)] += 1
            governance = self._cycle_field(cycle, "governance", {}) or {}
            admission = governance.get("admission", {}) if isinstance(governance, dict) else {}
            if admission:
                if admission.get("approved"):
                    admissions["approved"] += 1
                else:
                    admissions["rejected"] += 1
            else:
                admissions["unavailable"] += 1
            for proposal in governance.get("development_proposals", []) if isinstance(governance, dict) else []:
                title = str(proposal.get("title", "")).strip()
                if title:
                    proposals.setdefault(title.lower(), proposal)
            recent_decisions.append({
                "cycle_id": self._cycle_field(cycle, "cycle_id", ""),
                "category": category,
                "minted": bool(self._cycle_field(cycle, "minted", False)),
                "admission_approved": admission.get("approved") if admission else None,
            })

        return {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "controller": {
                "evaluation_samples": self.evaluation_samples,
                "agreement_threshold": self.agreement_threshold,
                "eligible_categories": list(self.categories),
            },
            "cycles_observed": len(records),
            "category_coverage": dict(sorted(category_coverage.items())),
            "admission": admissions,
            "open_proposals": list(proposals.values())[:50],
            "recent_decisions": recent_decisions[-20:],
        }

    @staticmethod
    def development_proposals(developer_analysis: Optional[Dict[str, Any]], cycle_id: str) -> List[Dict[str, Any]]:
        """Extract non-executable proposals from analysis for later human review."""
        if not isinstance(developer_analysis, dict):
            return []
        gaps = developer_analysis.get("research_gaps", []) or []
        proposals: List[Dict[str, Any]] = []
        for gap in gaps[:5]:
            title = str(gap).strip()
            if not title:
                continue
            proposals.append({
                "id": f"proposal-{cycle_id}-{len(proposals) + 1}",
                "title": title[:240],
                "status": "proposed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_cycle": cycle_id,
                "execution": "review_required",
                "scope": "research_or_documentation",
            })
        return proposals
