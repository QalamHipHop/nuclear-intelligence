"""Regression tests for the canonical runtime composition layer."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from core.runtime import DEFAULT_PROVIDER_CHAIN, RuntimeSettings, runtime_public_status


class RuntimeSettingsTests(unittest.TestCase):
    def test_defaults_are_shared_and_non_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = RuntimeSettings.from_environment(tmp)
        self.assertEqual(settings.provider_chain, DEFAULT_PROVIDER_CHAIN)
        self.assertEqual(settings.ledger_path.name, "virtual_ledger.json")
        self.assertEqual(settings.knowledge_graph_path.name, "knowledge_graph.json")
        self.assertGreaterEqual(settings.min_overall, 0)

    def test_environment_overrides_are_normalized(self) -> None:
        original = {k: os.environ.get(k) for k in ("NI_PROJECT_ROOT", "LLM_PROVIDER_CHAIN", "MIN_OVERALL", "DEVELOPER_MODE")}
        try:
            os.environ["NI_PROJECT_ROOT"] = "/tmp/ni-runtime-test"
            os.environ["LLM_PROVIDER_CHAIN"] = "groq, huggingface,"
            os.environ["MIN_OVERALL"] = "77.5"
            os.environ["DEVELOPER_MODE"] = "false"
            settings = RuntimeSettings.from_environment()
            self.assertEqual(settings.provider_chain, ("groq", "huggingface"))
            self.assertEqual(settings.min_overall, 77.5)
            self.assertFalse(settings.developer_mode)
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_public_status_exposes_no_secret_values(self) -> None:
        status = runtime_public_status(RuntimeSettings.from_environment("/tmp/ni-status"))
        rendered = repr(status)
        self.assertNotIn("HF_TOKEN", rendered)
        self.assertIn("canonical", rendered)
        self.assertIn("provider_chain", status)


if __name__ == "__main__":
    unittest.main()
