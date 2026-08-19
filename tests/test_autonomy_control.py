from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from core.autonomy_control import STOP_EXIT_CODE, guard, single_run_lock


class AutonomyControlTests(unittest.TestCase):
    def test_emergency_stop_blocks_execution(self) -> None:
        previous = os.environ.get("EMERGENCY_STOP")
        try:
            os.environ["EMERGENCY_STOP"] = "true"
            with tempfile.TemporaryDirectory() as tmp:
                self.assertEqual(guard(Path(tmp)), STOP_EXIT_CODE)
        finally:
            if previous is None:
                os.environ.pop("EMERGENCY_STOP", None)
            else:
                os.environ["EMERGENCY_STOP"] = previous

    def test_single_run_lock_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with single_run_lock(root):
                with self.assertRaises(RuntimeError):
                    with single_run_lock(root):
                        pass
            self.assertFalse((root / "knowledge_base" / ".autonomy.lock").exists())
            self.assertTrue((root / "knowledge_base" / "autonomy_control.json").exists())


if __name__ == "__main__":
    unittest.main()
