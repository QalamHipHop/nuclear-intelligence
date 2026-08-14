"""Fast, dependency-light tests for the hardened API surface."""
from __future__ import annotations

import os
import unittest

from api.health import app
from api.security import RateLimiter, valid_bearer_token


class ApiSecurityTests(unittest.TestCase):
    def test_expected_routes_exist(self) -> None:
        paths = {route.path for route in app.routes}
        self.assertTrue({"/health", "/ready", "/metrics", "/cycle"}.issubset(paths))

    def test_bearer_validation(self) -> None:
        self.assertTrue(valid_bearer_token("Bearer secret", "secret"))
        self.assertFalse(valid_bearer_token("Bearer wrong", "secret"))
        self.assertFalse(valid_bearer_token("Basic secret", "secret"))

    def test_rate_limiter(self) -> None:
        limiter = RateLimiter(limit=2, window_seconds=60)
        self.assertTrue(limiter.allow("client"))
        self.assertTrue(limiter.allow("client"))
        self.assertFalse(limiter.allow("client"))
        self.assertTrue(limiter.allow("other-client"))

    def test_api_key_is_opt_in(self) -> None:
        old = os.environ.pop("API_KEY", None)
        try:
            from api.security import configured_api_key
            self.assertIsNone(configured_api_key())
        finally:
            if old is not None:
                os.environ["API_KEY"] = old


if __name__ == "__main__":
    unittest.main()
