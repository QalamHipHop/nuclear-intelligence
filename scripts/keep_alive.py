"""Probe the live Space without holding a runner process open."""
from __future__ import annotations

import logging
import os
import sys
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SPACE_URL = os.getenv("SPACE_URL", "https://qalam-nuclear-intelligence.hf.space/")
HEALTH_URL = os.getenv("HEALTH_URL", SPACE_URL)


def probe(url: str) -> int:
    request = Request(url, headers={"User-Agent": "nuclear-intelligence-watchdog/1.0"})
    with urlopen(request, timeout=30) as response:
        return int(response.status)


def main() -> int:
    failures = []
    for label, url in (("space", SPACE_URL), ("health", HEALTH_URL)):
        try:
            status = probe(url)
            logger.info("%s status=%s url=%s", label, status, url)
            if status < 200 or status >= 400:
                failures.append(f"{label}:{status}")
        except Exception as exc:
            logger.error("%s probe failed: %s", label, type(exc).__name__)
            failures.append(f"{label}:error")
    if failures:
        logger.error("watchdog failed: %s", ",".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
