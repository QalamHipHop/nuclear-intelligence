#!/usr/bin/env python3
"""
Nuclear Intelligence v5.0 - Research Cycle Runner
═══════════════════════════════════════════════════════════════════
Runs a single research cycle. Two execution paths:

1. **GitHub Actions** (default): uses `core/` modules directly with FAISS RAG,
   multi-LLM fallback, advanced PoW mining, knowledge graph, and developer
   analysis. NEVER imports `hf_deploy/app.py` — that module is a Gradio UI
   entrypoint only.

2. **HF Space** (when `SPACE_ID` env var is set): uses the self-contained
   `core_hf.py` adapter which mirrors the HF-deploy pipeline but in a
   programmatic, import-safe form.

Both modes save a JSON report to `reports/`, push to the HF dataset if
`HF_TOKEN` is set, and commit results back to GitHub if `GITHUB_TOKEN` is set.
═══════════════════════════════════════════════════════════════════
"""
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logger.remove()
logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
)
# Ensure logs/ exists
Path("logs").mkdir(exist_ok=True)
logger.add("logs/cycle_runs.log", rotation="10 MB", level=LOG_LEVEL, encoding="utf-8")


def is_hf_space() -> bool:
    """Detect if we're actually running on a HuggingFace Space runtime."""
    return bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE") or os.getenv("RUNNING_ON_HF"))


def run_full_cycle() -> int:
    """Run a cycle using the full core/ pipeline (for GitHub Actions)."""
    from core.runtime import build_runtime

    logger.info("════════════════════════════════════════════════════════════")
    logger.info("⚛️  Nuclear Intelligence v5.0 — Full Pipeline (core/)")
    logger.info("════════════════════════════════════════════════════════════")

    core, loop, ledger, settings = build_runtime()
    result = loop.run_cycle(developer_mode=settings.developer_mode)

    # Pretty-print
    status = "✅ MINTED" if result.minted else "❌ REJECTED"
    elapsed = result.execution_time_seconds
    logger.info(f"Cycle {result.cycle_id} → {status} in {elapsed}s")

    if result.minted:
        logger.success(f"🪙 NES token minted: {result.tx_hash[:24]}...")
    else:
        logger.info("Cycle did not meet minting thresholds")

    return 0


def run_hf_cycle() -> int:
    """Run a cycle inside the HF Space runtime via a programmatic adapter.

    This path MUST NOT import `hf_deploy/app.py` because that module builds a
    full Gradio UI on import which (a) fails in non-UI contexts, and (b) is
    wasteful for a headless cycle run. We invoke `core_hf.HeadlessHFAdapter`
    instead, which exposes `run_cycle()` and `sync_to_hf_dataset()`.
    """
    from core_hf import HeadlessHFAdapter  # lazy import

    adapter = HeadlessHFAdapter()
    if not adapter.ready:
        logger.error("HF core not initialized (no API keys?); nothing to do.")
        return 1

    logger.info("════════════════════════════════════════════════════════════")
    logger.info("⚛️  Nuclear Intelligence v5.0 — HF Space Mode (headless)")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info(f"LLM providers: {adapter.providers}")
    logger.info(f"NES supply:    {adapter.nes_supply}")

    result = adapter.run_cycle()
    if "error" in result and "question" not in result:
        logger.error(f"Cycle failed: {result['error']}")
        return 1

    status = "✅ MINTED" if result.get("minted") else "❌ REJECTED"
    logger.info(
        f"Cycle {result['cycle_id']} → {status} in {result.get('execution_time_seconds', 0)}s"
    )

    if result.get("minted") and result.get("tx_hash"):
        logger.success(f"🪙 NES token minted: {result['tx_hash'][:24]}...")
        synced = adapter.sync_to_hf_dataset(result)
        logger.info(f"HF dataset sync: {'✅' if synced else '⚠️ skipped/failed'}")

    return 0


def refresh_developer_queue() -> None:
    """Generate a review-only developer queue from canonical proposals."""
    if os.getenv("AUTONOMOUS_DEVELOPER_ENABLED", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    try:
        from scripts.autonomous_developer import main as developer_main
        developer_main()
        logger.info("Autonomous developer queue refreshed (review-only)")
    except Exception:
        # Queue generation must never turn a valid research cycle into a false failure.
        logger.exception("Autonomous developer queue refresh failed safely")


def main() -> int:
    start = time.time()
    rc = 0
    try:
        from core.autonomy_control import guard
        root = Path(os.getenv("NI_PROJECT_ROOT", Path.cwd())).resolve()
        from core.autonomy_coordinator import coordination_status, may_run_cycles
        coordination = coordination_status("github")
        logger.info("Autonomy coordination: %s", coordination)
        if not may_run_cycles("github"):
            logger.warning("GitHub runner is not the configured autonomous orchestrator")
            return 0
        stop_code = guard(root)

        if stop_code:
            logger.warning("Autonomous execution blocked by control guard")
            return stop_code
        if is_hf_space():
            rc = run_hf_cycle()
        else:
            rc = run_full_cycle()
        refresh_developer_queue()
    except Exception as e:
        logger.exception(f"Fatal cycle error: {e}")
        rc = 1
    elapsed = time.time() - start
    logger.info(f"════════ Cycle finished in {elapsed:.1f}s (rc={rc}) ════════════")
    return rc


if __name__ == "__main__":
    sys.exit(main())
