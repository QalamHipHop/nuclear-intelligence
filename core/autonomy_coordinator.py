"""Single-orchestrator contract for autonomous execution.

The repository may expose several runtimes, but only one scheduler is allowed to
run durable research cycles at a time. The default coordinator is GitHub Actions;
the Space remains a read/restore/health surface and never duplicates scheduled work.
"""
from __future__ import annotations

import os
from typing import Literal

Role = Literal["github", "space", "external", "disabled"]


def orchestrator_role() -> Role:
    value = os.getenv("AUTONOMY_ORCHESTRATOR", "github").strip().lower()
    return value if value in {"github", "space", "external", "disabled"} else "disabled"  # type: ignore[return-value]


def may_run_cycles(runtime: Role) -> bool:
    """Return whether this runtime owns durable autonomous cycles."""
    role = orchestrator_role()
    return role == runtime and role != "disabled"


def coordination_status(runtime: Role) -> dict[str, object]:
    role = orchestrator_role()
    return {
        "configured_orchestrator": role,
        "runtime": runtime,
        "owns_cycles": may_run_cycles(runtime),
        "single_writer": True,
    }
