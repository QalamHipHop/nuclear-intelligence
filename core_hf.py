"""Import-safe Hugging Face adapter over the canonical Nuclear Intelligence runtime.

The Space UI uses this module only as a presentation gateway. Research, safety,
evaluation, knowledge graph, ledger and governance decisions remain implemented
once in the repository's canonical runtime.
"""
from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from threading import RLock
from typing import Any, Dict, List, Optional

from core.runtime import RuntimeSettings, build_runtime, runtime_public_status
from core.runtime_config import validate_secret
from core.safety_guard import check_answer, check_query, render_safe_block

try:
    from loguru import logger
except Exception:  # pragma: no cover
    import logging
    logger = logging.getLogger("core_hf")


class HeadlessHFAdapter:
    """Small, presentation-safe facade over the canonical research runtime."""

    def __init__(self) -> None:
        self._core = None
        self._loop = None
        self._ledger = None
        self.settings: Optional[RuntimeSettings] = None
        self._load_error: Optional[str] = None
        self._work_lock = RLock()
        self._public_events: deque[float] = deque()
        self._load()

    @property
    def ready(self) -> bool:
        return self._core is not None and self._loop is not None and self._ledger is not None

    @property
    def providers(self) -> List[str]:
        if not self._core:
            return []
        return list(
            getattr(self._core.llm, "_available_providers", None)
            or getattr(self._core.llm, "_available", [])
            or []
        )

    @property
    def nes_supply(self) -> float:
        return float(getattr(self._ledger, "nes_supply", 0.0)) if self._ledger else 0.0

    def _load(self) -> None:
        try:
            self._core, self._loop, self._ledger, self.settings = build_runtime()
            logger.info("Canonical HF adapter ready · providers=%s · nes=%s", self.providers, self.nes_supply)
        except Exception as exc:  # pragma: no cover
            self._load_error = str(exc)
            logger.exception("Canonical HF adapter initialization failed")

    def _unavailable(self) -> Optional[Dict[str, Any]]:
        if not self.ready:
            return {"error": f"canonical runtime not initialized: {self._load_error or 'unknown error'}"}
        return None

    def public_status(self) -> Dict[str, Any]:
        status = runtime_public_status(self.settings) if self.settings else {"runtime": "canonical"}
        status.update({
            "ready": self.ready,
            "providers": self.providers,
            "nes_supply": self.nes_supply,
            # Never expose exception text, filesystem paths or provider errors.
            "degraded": bool(self._load_error),
        })
        return status

    def system_stats(self) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        return {
            "runtime": self.public_status(),
            "core": self._core.get_stats(),
            "loop": self._loop.get_stats(),
            "ledger": self._ledger.get_stats(),
        }

    def governance(self) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        return self._loop.controller.governance_snapshot(self._loop.history)

    def _allow_public_request(self) -> bool:
        """Apply a small in-process sliding-window guard to public callbacks."""
        limit = int(getattr(self.settings, "public_rate_limit_per_minute", 20) or 20)
        now = time.monotonic()
        with self._work_lock:
            while self._public_events and now - self._public_events[0] >= 60:
                self._public_events.popleft()
            if len(self._public_events) >= limit:
                return False
            self._public_events.append(now)
            return True

    def recent_cycles(self, limit: int = 25) -> List[Dict[str, Any]]:
        unavailable = self._unavailable()
        if unavailable:
            return [unavailable]
        return self._loop.get_recent_cycles(max(1, min(int(limit), 100)))[::-1]

    def knowledge_search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        unavailable = self._unavailable()
        if unavailable:
            return [unavailable]
        cleaned = " ".join((query or "").split())
        if not cleaned:
            return []
        max_chars = int(getattr(self.settings, "public_max_query_chars", 2000) or 2000)
        if len(cleaned) > max_chars:
            return [{"error": f"Query exceeds the public limit of {max_chars} characters."}]
        if not self._allow_public_request():
            return [{"error": "Public request limit reached; please retry later."}]
        return self._core.kg.search(cleaned, max(1, min(int(limit), 50)))

    def ledger_status(self) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        return {"valid": self._ledger.is_chain_valid(), **self._ledger.get_stats()}

    def run_cycle(self, dev_mode: Optional[bool] = None, *, public: bool = False) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        if public and not bool(getattr(self.settings, "public_cycle_enabled", False)):
            return {"error": "Public autonomous cycles are disabled; use the read-only research interface."}
        if public and not self._allow_public_request():
            return {"error": "Public request limit reached; please retry later."}
        with self._work_lock:
            try:
                use_dev_mode = self.settings.developer_mode if dev_mode is None else bool(dev_mode)
                return self._loop.run_cycle(developer_mode=use_dev_mode).to_dict()
            except Exception:
                logger.exception("Canonical HF run_cycle failed")
                return {"error": "The governed cycle failed safely; inspect operator logs."}

    def ask_question(self, question: str, developer_mode: bool = False) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        cleaned = " ".join((question or "").split())
        max_chars = int(getattr(self.settings, "public_max_query_chars", 2000) or 2000)
        if len(cleaned) < 5:
            return {"error": "Enter a question of at least five characters."}
        if len(cleaned) > max_chars:
            return {"error": f"Question exceeds the public limit of {max_chars} characters."}
        if not self._allow_public_request():
            return {"error": "Public request limit reached; please retry later."}
        query_verdict = check_query(cleaned)
        if not query_verdict.allowed:
            return {"refused": True, "message": render_safe_block(query_verdict), "verdict": query_verdict.to_dict()}
        with self._work_lock:
            try:
                result = self._core.ask_question(
                    cleaned,
                    developer_mode=bool(developer_mode),
                    use_web_search=self.settings.web_search_enabled,
                )
                answer_verdict = check_answer(str(result.get("answer", "")))
                if not answer_verdict.allowed:
                    return {"refused": True, "message": render_safe_block(answer_verdict), "verdict": answer_verdict.to_dict()}
                result["safety"] = {"allowed": True}
                return result
            except Exception:
                logger.exception("Canonical HF manual research failed")
                return {"error": "The research request failed safely; inspect operator logs."}

    def export_state(self, limit: int = 25) -> Dict[str, Any]:
        unavailable = self._unavailable()
        if unavailable:
            return unavailable
        return {
            "exported_at": __import__("datetime").datetime.now().isoformat(),
            "stats": self.system_stats(),
            "governance": self.governance(),
            "recent_cycles": self.recent_cycles(limit),
        }

    def sync_to_hf_dataset(self, report: Dict[str, Any]) -> bool:
        """Persist a report and invoke the single repository sync implementation."""
        if not validate_secret("HF_TOKEN", prefix="hf_").usable:
            logger.warning("HF sync unavailable: HF_TOKEN is not configured")
            return False
        try:
            root = self.settings.root if self.settings else Path.cwd()
            reports_dir = root / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = reports_dir / f"cycle_{report['cycle_id']}.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            from scripts.sync_huggingface import sync_hf_dataset
            return sync_hf_dataset(limit=1) == 0
        except Exception as exc:
            logger.warning("HF dataset sync failed: %s", exc)
            return False


_DEFAULT_ADAPTER: Optional[HeadlessHFAdapter] = None


def get_adapter() -> HeadlessHFAdapter:
    global _DEFAULT_ADAPTER
    if _DEFAULT_ADAPTER is None:
        _DEFAULT_ADAPTER = HeadlessHFAdapter()
    return _DEFAULT_ADAPTER


def run_cycle(dev_mode: Optional[bool] = None) -> Dict[str, Any]:
    return get_adapter().run_cycle(dev_mode=dev_mode)


def sync_to_hf_dataset(report: Dict[str, Any]) -> bool:
    return get_adapter().sync_to_hf_dataset(report)
