from __future__ import annotations

import os
import tempfile
import unittest
from types import SimpleNamespace

from core.nuclear_intelligence_v4 import EvaluationScore, ResearchAnswer, ResearchQuestion
from core.operation_loop_v4 import OperationLoop, OperationLoopConfig


class _Core:
    def __init__(self) -> None:
        self.kg = SimpleNamespace(graph={"entities": {}})
        self.category_hint = ""
        self.integrated = False

    def generate_question(self, category_hint: str = "") -> ResearchQuestion:
        self.category_hint = category_hint
        return ResearchQuestion(
            question="How can passive safety improve small modular reactor resilience?",
            category=category_hint or "Safety",
            difficulty=7,
            keywords=["SMR", "passive safety"],
        )

    def conduct_research(self, question: ResearchQuestion, use_web_search: bool = True) -> ResearchAnswer:
        return ResearchAnswer(
            answer=(
                "IAEA safety guidance (2024) [1] and peer-reviewed evidence [2] support passive systems. "
                "The supporting evidence is indexed by DOI 10.1000/example."
            ),
            citations=["IAEA safety guidance 2024", "https://doi.org/10.1000/example"],
            novelty_score=100,
            accuracy_score=100,
            sources=[],
            provider="groq",
        )

    def evaluate_answer(self, question: ResearchQuestion, answer: ResearchAnswer) -> EvaluationScore:
        return EvaluationScore(
            scientific_accuracy=100,
            novelty_score=100,
            usefulness_score=100,
            self_consistency_check=True,
            justification="independent evaluation",
            completeness=100,
        )

    def developer_mode_analysis(self, question: ResearchQuestion, answer: ResearchAnswer):
        return {"research_gaps": ["Publish a reactor-safety evidence index"]}

    def integrate_knowledge(self, question: ResearchQuestion, answer: ResearchAnswer, evaluation: EvaluationScore) -> None:
        self.integrated = True

    def reject_answer(self, evaluation: EvaluationScore) -> None:
        raise AssertionError("High-quality evidence should pass the enhanced gate")


class _Ledger:
    def __init__(self) -> None:
        self.payload = None

    def mint_nes_token(self, payload):
        self.payload = payload
        return "test-transaction"


class OperationLoopControllerTests(unittest.TestCase):
    def test_controller_drives_cycle_and_persists_governance(self) -> None:
        core = _Core()
        ledger = _Ledger()
        config = OperationLoopConfig(
            save_reports=False,
            developer_mode=True,
            evaluation_samples=2,
            min_accuracy=70,
            min_novelty=60,
            min_usefulness=60,
            min_overall=65,
        )
        with tempfile.TemporaryDirectory() as tmp, _temporary_directory(tmp):
            loop = OperationLoop(core, ledger, config)
            result = loop.run_cycle()

        self.assertTrue(result.minted)
        self.assertTrue(core.integrated)
        self.assertIn(core.category_hint, loop.controller.categories)
        self.assertTrue(result.governance["admission"]["approved"])
        self.assertEqual(result.governance["development_proposals"][0]["status"], "proposed")
        self.assertEqual(ledger.payload["governance"]["agenda"]["selected_category"], core.category_hint)


class _temporary_directory:
    def __init__(self, path: str) -> None:
        self.path = path
        self.previous = ""

    def __enter__(self):
        self.previous = os.getcwd()
        os.chdir(self.path)

    def __exit__(self, exc_type, exc, tb):
        os.chdir(self.previous)


if __name__ == "__main__":
    unittest.main()
