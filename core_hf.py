"""
Nuclear Intelligence v5.0 - Headless HF Adapter
═══════════════════════════════════════════════════════════════════
Programmatic, import-safe entrypoint used by `run_operation_cycle.py`
when running inside the HuggingFace Space runtime.  It exposes the
exact same surface area that the legacy `hf_deploy/app.py` provided
(`run_cycle`, `sync_to_hf_dataset`, `core.*`) but does NOT instantiate
the Gradio UI, so it is safe to import from non-UI contexts (CI, GH
Actions cycles, headless cron, etc.).
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make sure `hf_deploy/` is importable so we can reuse the battle-tested
# LLMEngine / VirtualLedger / KnowledgeGraph implementations that ship
# with the Space.
_HERE = Path(__file__).parent
_HF_DEPLOY = _HERE / "hf_deploy"
if str(_HF_DEPLOY) not in sys.path:
    sys.path.insert(0, str(_HF_DEPLOY))

try:
    from loguru import logger  # type: ignore
except Exception:  # pragma: no cover
    import logging as _logging  # noqa: WPS433

    logger = _logging.getLogger("core_hf")  # type: ignore[assignment]
    if not logger.handlers:
        _h = _logging.StreamHandler()
        _h.setFormatter(_logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(_h)
        logger.setLevel(_logging.INFO)


class HeadlessHFAdapter:
    """Headless mirror of the HF Space pipeline.

    Wraps the `NuclearIntelligenceCore` from `hf_deploy/app.py` in a
    safe loader: if Gradio is unavailable, the class still imports
    because the Gradio UI is built lazily under ``if gradio_available``.
    """

    def __init__(self) -> None:
        self._core: Optional[Any] = None
        self._load_error: Optional[str] = None
        self._load()

    # ── public properties ────────────────────────────────────────
    @property
    def ready(self) -> bool:
        return self._core is not None

    @property
    def providers(self) -> List[str]:
        if not self._core:
            return []
        return list(getattr(self._core.llm, "_available", []) or [])

    @property
    def nes_supply(self) -> float:
        if not self._core:
            return 0.0
        try:
            return float(self._core.ledger.nes_supply)
        except Exception:
            return 0.0

    # ── lifecycle ────────────────────────────────────────────────
    def _load(self) -> None:
        try:
            # Importing `app` is safe because the UI block is now
            # guarded by `if gradio_available:`.
            from app import NuclearIntelligenceCore  # type: ignore  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            self._load_error = f"{exc}\n{traceback.format_exc()}"
            logger.error(f"HeadlessHFAdapter: failed to import hf_deploy.app: {exc}")
            return

        try:
            self._core = NuclearIntelligenceCore()
            real = [p for p in self.providers if p != "demo"]
            logger.info(f"HeadlessHFAdapter ready · providers={real or 'demo'} · nes={self.nes_supply}")
        except Exception as exc:
            self._load_error = str(exc)
            logger.error(f"HeadlessHFAdapter: core init failed: {exc}")

    # ── public API ───────────────────────────────────────────────
    def run_cycle(self, dev_mode: bool = True) -> Dict[str, Any]:
        if not self._core:
            return {"error": f"core not initialized: {self._load_error}"}
        try:
            return self._core.run_cycle(dev_mode=dev_mode)
        except Exception as exc:
            logger.exception("run_cycle failed")
            return {"error": str(exc), "traceback": traceback.format_exc()}

    def sync_to_hf_dataset(self, report: Dict[str, Any]) -> bool:
        """Mirror the legacy `sync_to_hf_dataset(report)` helper.

        Kept self-contained so we do not have to import the Gradio
        module-level helper.
        """
        try:
            from huggingface_hub import HfApi, create_repo  # type: ignore
        except Exception as exc:
            logger.warning(f"sync_to_hf_dataset: huggingface_hub unavailable: {exc}")
            return False

        hf_token = os.getenv("HF_TOKEN", "").strip()
        if not hf_token or not hf_token.startswith("hf_"):
            return False

        try:
            api = HfApi(token=hf_token)
            dataset_repo = os.getenv("HF_DATASET_REPO", "Qalam/nuclear-intelligence-dataset")
            try:
                create_repo(
                    repo_id=dataset_repo,
                    repo_type="dataset",
                    token=hf_token,
                    exist_ok=True,
                    private=False,
                )
            except Exception:
                pass

            os.makedirs("reports", exist_ok=True)
            fname = f"cycle_{report['cycle_id']}.json"
            local_path = os.path.join("reports", fname)
            with open(local_path, "w", encoding="utf-8") as fh:
                json.dump(report, fh, ensure_ascii=False, indent=4)

            api.upload_file(
                path_or_fileobj=local_path,
                path_in_repo=f"reports/{fname}",
                repo_id=dataset_repo,
                repo_type="dataset",
                commit_message=f"Auto: NES cycle {report['cycle_id']}",
            )
            return True
        except Exception as exc:
            logger.warning(f"sync_to_hf_dataset failed: {exc}")
            return False


# ── module-level shortcuts (back-compat) ──────────────────────────
_DEFAULT_ADAPTER: Optional[HeadlessHFAdapter] = None


def _get_adapter() -> HeadlessHFAdapter:
    global _DEFAULT_ADAPTER
    if _DEFAULT_ADAPTER is None:
        _DEFAULT_ADAPTER = HeadlessHFAdapter()
    return _DEFAULT_ADAPTER


def run_cycle(dev_mode: bool = True) -> Dict[str, Any]:
    """Module-level convenience: runs one cycle via the shared adapter."""
    return _get_adapter().run_cycle(dev_mode=dev_mode)


def sync_to_hf_dataset(report: Dict[str, Any]) -> bool:
    return _get_adapter().sync_to_hf_dataset(report)
