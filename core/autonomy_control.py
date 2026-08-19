"""Bounded controls for autonomous research execution.

This module deliberately controls orchestration only. It cannot weaken safety
policies, evaluation thresholds, credential rules or ledger admission gates.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


STOP_EXIT_CODE = 78


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def autonomy_enabled() -> bool:
    return _truthy(os.getenv("AUTONOMY_ENABLED"), default=True)


def emergency_stop_active() -> bool:
    return _truthy(os.getenv("EMERGENCY_STOP"), default=False)


def _state_path(root: Path) -> Path:
    return root / "knowledge_base" / "autonomy_control.json"


def record_event(root: Path, event: str, **details: object) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "details": details,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@contextmanager
def single_run_lock(root: Path) -> Iterator[None]:
    """Acquire a process lock without leaving a stale lock after normal exit."""
    path = root / "knowledge_base" / ".autonomy.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError("another autonomous run is already active") from exc
    try:
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        record_event(root, "started", pid=os.getpid())
        yield
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        record_event(root, "finished", pid=os.getpid())


def guard(root: Path) -> int:
    if not autonomy_enabled():
        record_event(root, "disabled")
        return STOP_EXIT_CODE
    if emergency_stop_active():
        record_event(root, "emergency_stop")
        return STOP_EXIT_CODE
    return 0
