from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.build_space_bundle import build_bundle


class SpaceBundleTests(unittest.TestCase):
    def test_bundle_contains_canonical_runtime_and_thin_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle = build_bundle(Path(temporary) / "space")
            for required in (
                "app.py",
                "core_hf.py",
                "core/runtime.py",
                "core/research_controller.py",
                "core/operation_loop_v4.py",
                "blockchain/virtual_ledger.py",
                "requirements.txt",
                "Dockerfile",
            ):
                self.assertTrue((bundle / required).exists(), required)

            app_source = (bundle / "app.py").read_text(encoding="utf-8")
            self.assertIn("from core_hf import get_adapter", app_source)
            self.assertNotIn("class NuclearIntelligenceCore", app_source)
            self.assertNotIn("def _autonomous_loop", app_source)

    def test_bundle_is_not_written_into_project_root(self) -> None:
        from scripts.build_space_bundle import ROOT
        with self.assertRaises(ValueError):
            build_bundle(ROOT)


if __name__ == "__main__":
    unittest.main()
