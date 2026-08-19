from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from core.runtime import RuntimeSettings, runtime_public_status


class PublicControlTests(unittest.TestCase):
    def test_public_status_omits_filesystem_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = RuntimeSettings.from_environment(tmp)
            status = runtime_public_status(settings)
        self.assertNotIn("root", status)
        self.assertNotIn("paths", status)
        self.assertIn("public_max_query_chars", status["thresholds"])

    def test_public_controls_are_bounded(self) -> None:
        previous = {key: os.environ.get(key) for key in ("PUBLIC_MAX_QUERY_CHARS", "PUBLIC_RATE_LIMIT_PER_MINUTE")}
        try:
            os.environ["PUBLIC_MAX_QUERY_CHARS"] = "999999"
            os.environ["PUBLIC_RATE_LIMIT_PER_MINUTE"] = "0"
            settings = RuntimeSettings.from_environment(Path(tempfile.gettempdir()) / "ni-controls")
            self.assertEqual(settings.public_max_query_chars, 4000)
            self.assertEqual(settings.public_rate_limit_per_minute, 1)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
