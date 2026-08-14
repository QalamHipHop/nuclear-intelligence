"""Regression tests for the no-fallback-minting safety invariant."""
from __future__ import annotations

import unittest

from core.nuclear_intelligence_v4 import EvaluationScore, ResearchAnswer
from core.operation_loop_v4 import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger


class NoFallbackMintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = OperationLoop.__new__(OperationLoop)
        self.loop.config = OperationLoopConfig(
            min_accuracy=70, min_novelty=60, min_usefulness=60,
            min_overall=65, min_completeness=40,
        )

    def test_fallback_provider_is_rejected(self) -> None:
        evaluation = EvaluationScore(95, 85, 90, True, "real evaluator", 90)
        answer = ResearchAnswer(
            answer="fallback", citations=[], novelty_score=85,
            accuracy_score=95, sources=[], provider="fallback",
        )
        decision = self.loop._should_mint(evaluation, answer)
        self.assertFalse(decision["should_mint"])

    def test_unavailable_evaluator_is_rejected(self) -> None:
        evaluation = EvaluationScore(
            0, 0, 0, False,
            "Evaluation unavailable; minting disabled until a real evaluator responds.",
            0,
        )
        answer = ResearchAnswer(
            answer="real-looking text", citations=[], novelty_score=0,
            accuracy_score=0, sources=[], provider="groq",
        )
        decision = self.loop._should_mint(evaluation, answer)
        self.assertFalse(decision["should_mint"])


if __name__ == "__main__":
    unittest.main()
