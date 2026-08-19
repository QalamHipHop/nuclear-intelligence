"""Run one bounded autonomous research tick.

The scheduler calls this script. It performs one canonical cycle only and exits;
it does not become an unbounded daemon and it never publishes secrets.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from core.autonomy_control import guard, record_event, single_run_lock
from core.runtime import build_runtime


def main() -> int:
    root = Path(os.getenv("NI_PROJECT_ROOT", Path.cwd())).resolve()
    stop_code = guard(root)
    if stop_code:
        return stop_code
    try:
        with single_run_lock(root):
            _, loop, _, settings = build_runtime()
            result = loop.run_cycle(developer_mode=settings.developer_mode)
            payload = result.to_dict()
            record_event(
                root,
                "cycle_completed",
                cycle_id=payload.get("cycle_id"),
                minted=bool(payload.get("minted")),
                provider=payload.get("answer", {}).get("provider"),
            )
            print(payload.get("cycle_id", "cycle-complete"))
            return 0
    except Exception as exc:
        record_event(root, "cycle_failed", error_type=type(exc).__name__)
        print("autonomous cycle failed safely", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
