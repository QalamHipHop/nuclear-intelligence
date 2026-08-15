from __future__ import annotations

import unittest

from core.nuclear_intelligence_v4 import EvaluationScore, ResearchAnswer, ResearchQuestion
from core.research_controller import ResearchController


class ResearchControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ResearchController(categories=("Fusion", "Safety", "Waste"), evaluation_samples=2)

    def test_manual_hint_has_priority(self) -> None:
        decision = self.controller.select_next_category([], manual_hint="Safety")
        self.assertEqual(decision.selected_category, "Safety")
        self.assertIn("manual", decision.reason)

    def test_agenda_avoids_overrepresented_category(self) -> None:
        history = [
            {"question": {"category": "Fusion"}, "minted": True},
            {"question": {"category": "Fusion"}, "minted": True},
            {"question": {"category": "Fusion"}, "minted": False},
        ]
        decision = self.controller.select_next_category(history)
        self.assertNotEqual(decision.selected_category, "Fusion")
        self.assertEqual(set(decision.category_scores), {"Fusion", "Safety", "Waste"})

    def test_snapshot_tracks_decisions_and_deduplicates_proposals(self) -> None:
        history = [
            {
                "cycle_id": "cycle-1",
                "question": {"category": "Safety"},
                "minted": True,
                "governance": {
                    "admission": {"approved": True},
                    "development_proposals": [{"title": "Publish a safety evidence index", "status": "proposed"}],
                },
            },
            {
                "cycle_id": "cycle-2",
                "question": {"category": "Safety"},
                "minted": False,
                "governance": {
                    "admission": {"approved": False},
                    "development_proposals": [{"title": "Publish a safety evidence index", "status": "proposed"}],
                },
            },
        ]
        snapshot = self.controller.governance_snapshot(history)
        self.assertEqual(snapshot["category_coverage"]["Safety"], 2)
        self.assertEqual(snapshot["admission"], {"approved": 1, "rejected": 1, "unavailable": 0})
        self.assertEqual(len(snapshot["open_proposals"]), 1)

    def test_fallback_provider_never_passes_gate(self) -> None:
        question = ResearchQuestion(question="How can reactor safety analysis be improved?", category="Safety", difficulty=6, keywords=[])
        answer = ResearchAnswer(
            answer="The IAEA (2024) guidance [1] and DOI 10.1000/example support independent safety analysis.",
            citations=["IAEA safety guidance 2024", "https://doi.org/10.1000/example"],
            novelty_score=100,
            accuracy_score=100,
            sources=[],
            provider="fallback",
        )
        score = EvaluationScore(
            scientific_accuracy=100,
            novelty_score=100,
            usefulness_score=100,
            self_consistency_check=True,
            justification="independent evaluation",
            completeness=100,
        )
        gate = self.controller.enhanced_gate(question, answer, [score, score])
        self.assertFalse(gate["approved"])
        self.assertIn("non-production research provider", gate["reasons"])

    def test_high_quality_real_answer_passes_gate(self) -> None:
        question = ResearchQuestion(question="How can passive safety support small modular reactors?", category="Safety", difficulty=7, keywords=[])
        answer = ResearchAnswer(
            answer=(
                "IAEA guidance (2024) [1] and peer-reviewed evidence [2] describe passive safety. "
                "The evidence is indexed by DOI 10.1000/example."
            ),
            citations=["IAEA safety guidance 2024", "https://doi.org/10.1000/example"],
            novelty_score=100,
            accuracy_score=100,
            sources=[],
            provider="groq",
        )
        score = EvaluationScore(
            scientific_accuracy=100,
            novelty_score=100,
            usefulness_score=100,
            self_consistency_check=True,
            justification="independent evaluation",
            completeness=100,
        )
        gate = self.controller.enhanced_gate(question, answer, [score, score])
        self.assertTrue(gate["approved"])
        self.assertTrue(gate["readiness"]["ready_to_mint"])


if __name__ == "__main__":
    unittest.main()
