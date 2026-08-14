"""Canonical headless adapter for Hugging Face Spaces.

The Space runtime uses the same core, operation loop, ledger and settings as
CLI/API/GitHub Actions. The Gradio UI is only a presentation layer and is not
a second research implementation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.runtime import RuntimeSettings, build_runtime
from core.runtime_config import read_secret, validate_secret

try:
    from loguru import logger
except Exception:  # pragma: no cover
    import logging
    logger = logging.getLogger("core_hf")


class HeadlessHFAdapter:
    """Import-safe adapter over the canonical Nuclear Intelligence runtime."""

    def __init__(self) -> None:
        self._core = None
        self._loop = None
        self._ledger = None
        self.settings: Optional[RuntimeSettings] = None
        self._load_error: Optional[str] = None
        self._load()

    @property
    def ready(self) -> bool:
        return self._core is not None and self._loop is not None and self._ledger is not None

    @property
    def providers(self) -> List[str]:
        if not self._core:
            return []
        return list(getattr(self._core.llm, "_available_providers", []) or [])

    @property
    def nes_supply(self) -> float:
        if not self._ledger:
            return 0.0
        return float(getattr(self._ledger, "nes_supply", 0.0))

    def _load(self) -> None:
        try:
            self._core, self._loop, self._ledger, self.settings = build_runtime()
            logger.info(f"Canonical HF adapter ready · providers={self.providers} · nes={self.nes_supply}")
        except Exception as exc:  # pragma: no cover
            self._load_error = str(exc)
            logger.exception("Canonical HF adapter initialization failed")

    def run_cycle(self, dev_mode: Optional[bool] = None) -> Dict[str, Any]:
        if not self.ready:
            return {"error": f"canonical runtime not initialized: {self._load_error}"}
        try:
            use_dev_mode = self.settings.developer_mode if dev_mode is None else dev_mode
            result = self._loop.run_cycle(developer_mode=use_dev_mode)
            return result.to_dict()
        except Exception as exc:
            logger.exception("canonical HF run_cycle failed")
            return {"error": str(exc)}

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


def _get_adapter() -> HeadlessHFAdapter:
    global _DEFAULT_ADAPTER
    if _DEFAULT_ADAPTER is None:
        _DEFAULT_ADAPTER = HeadlessHFAdapter()
    return _DEFAULT_ADAPTER


_DEFAULT_ADAPTER: Optional[HeadlessHFAdapter] = None


def run_cycle(dev_mode: Optional[bool] = None) -> Dict[str, Any]:
    return _get_adapter().run_cycle(dev_mode=dev_mode)


def sync_to_hf_dataset(report: Dict[str, Any]) -> bool:
    return _get_adapter().sync_to_hf_dataset(report)
