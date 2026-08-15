from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


class SpaceUiImportTests(unittest.TestCase):
    def test_thin_space_ui_builds_without_duplicate_engine(self) -> None:
        app_path = Path(__file__).resolve().parent.parent / "hf_deploy" / "space_app.py"
        with tempfile.TemporaryDirectory() as temporary:
            previous_root = os.environ.get("NI_PROJECT_ROOT")
            os.environ["NI_PROJECT_ROOT"] = temporary
            try:
                spec = importlib.util.spec_from_file_location("space_ui_test", app_path)
                self.assertIsNotNone(spec)
                self.assertIsNotNone(spec.loader)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertIsNotNone(module.demo)
                self.assertNotIn("NuclearIntelligenceCore", module.__dict__)
            finally:
                if previous_root is None:
                    os.environ.pop("NI_PROJECT_ROOT", None)
                else:
                    os.environ["NI_PROJECT_ROOT"] = previous_root


if __name__ == "__main__":
    unittest.main()
