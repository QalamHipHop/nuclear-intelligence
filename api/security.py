"""Small, dependency-free security primitives for the Nuclear Intelligence API.

The API remains usable in local development when API_KEY is unset. In hosted
production deployments, setting API_KEY enables constant-time bearer-key
validation and a bounded in-memory rate limiter.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional


class RateLimiter:
    """Thread-safe fixed-window limiter keyed by client identifier."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            # Prevent unbounded memory growth from one-off client identifiers.
            if len(self._events) > 10_000:
                stale = [k for k, values in self._events.items() if not values or values[-1] <= cutoff]
                for stale_key in stale[:2_000]:
                    self._events.pop(stale_key, None)
            return True


def configured_api_key() -> Optional[str]:
    value = os.getenv("API_KEY", "").strip()
    return value if value and not value.lower().startswith("your_") else None


def valid_bearer_token(authorization: Optional[str], expected: Optional[str] = None) -> bool:
    """Validate an Authorization: Bearer header using constant-time comparison."""
    expected = expected or configured_api_key()
    if not expected or not authorization:
        return False
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return False
    return hmac.compare_digest(
        hashlib.sha256(token.strip().encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )
