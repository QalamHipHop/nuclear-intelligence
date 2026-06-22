#!/usr/bin/env python3
"""
Nuclear Intelligence v5.0 - Research Cycle Runner
═══════════════════════════════════════════════════════════════════
Runs a single research cycle. Works in two modes:

1. **Full mode** (default): uses `core/` modules with FAISS RAG, multi-LLM
   fallback, advanced PoW mining, knowledge graph, and developer analysis.
2. **HF Space mode** (when `SPACE_ID` env var is set): uses the lightweight
   `hf_deploy/app.py` self-contained core.

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
logger.add(sys.stdout, level=LOG_LEVEL, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>")
logger.add("logs/cycle_runs.log", rotation="10 MB", level=LOG_LEVEL, encoding="utf-8")


def is_hf_space() -> bool:
    return bool(os.getenv("SPACE_ID") or os.getenv("HF_SPACE") or os.getenv("HF_TOKEN") and not os.getenv("GH_TOKEN"))


def run_full_cycle() -> int:
    """Run a cycle using the full core/ pipeline (for GitHub Actions)."""
    from core.nuclear_intelligence import NuclearIntelligenceCore
    from core.operation_loop import OperationLoop, OperationLoopConfig
    from blockchain.virtual_ledger import VirtualLedger

    logger.info("════════════════════════════════════════════════════════════")
    logger.info("⚛️  Nuclear Intelligence v5.0 — Full Pipeline")
    logger.info("════════════════════════════════════════════════════════════")

    config = OperationLoopConfig(
        interval_minutes=int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", "30")),
        min_accuracy=float(os.getenv("MIN_ACCURACY", "70")),
        min_novelty=float(os.getenv("MIN_NOVELTY", "60")),
        min_usefulness=float(os.getenv("MIN_USEFULNESS", "60")),
        min_overall=float(os.getenv("MIN_OVERALL", "65")),
        min_completeness=float(os.getenv("MIN_COMPLETENESS", "40")),
        questions_per_cycle=1,
        developer_mode=os.getenv("DEVELOPER_MODE", "true").lower() == "true",
        web_search_enabled=True,
        save_reports=True,
        max_retries=3,
        retry_delay=5,
        sync_to_hf=True,
        sync_to_gh=True,
    )

    core = NuclearIntelligenceCore(
        provider_chain=[
            "huggingface", "deepseek", "groq", "gemini",
            "together", "fireworks", "aimlapi",
        ],
    )
    ledger = VirtualLedger(
        ledger_file="knowledge_base/virtual_ledger.json",
        difficulty=int(os.getenv("POW_DIFFICULTY", "3")),
    )
    loop = OperationLoop(core=core, ledger=ledger, config=config)

    result = loop.run_cycle(developer_mode=config.developer_mode)

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
    """Run a cycle using the HF-deploy self-contained core."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hf_app",
        str(Path(__file__).parent.parent / "hf_deploy" / "app.py"),
    )
    hf_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf_app)

    if not hf_app.core:
        logger.error("HF core not initialized")
        return 1

    logger.info("════════════════════════════════════════════════════════════")
    logger.info("⚛️  Nuclear Intelligence v5.0 — HF Space Mode")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info(f"LLM providers: {hf_app.core.llm._available}")
    logger.info(f"NES supply: {hf_app.core.ledger.nes_supply}")

    result = hf_app.core.run_cycle(dev_mode=True)

    if "error" in result and "question" not in result:
        logger.error(f"Cycle failed: {result['error']}")
        return 1

    status = "✅ MINTED" if result.get("minted") else "❌ REJECTED"
    logger.info(f"Cycle {result['cycle_id']} → {status} in {result.get('execution_time_seconds', 0)}s")

    if result.get("minted") and result.get("tx_hash"):
        logger.success(f"🪙 NES token minted: {result['tx_hash'][:24]}...")
        # Auto-sync to HF dataset
        synced = hf_app.sync_to_hf_dataset(result)
        logger.info(f"HF dataset sync: {'✅' if synced else '⚠️ skipped/failed'}")

    return 0


def main() -> int:
    start = time.time()
    try:
        if is_hf_space():
            rc = run_hf_cycle()
        else:
            rc = run_full_cycle()
    except Exception as e:
        logger.exception(f"Fatal cycle error: {e}")
        rc = 1
    elapsed = time.time() - start
    logger.info(f"════════ Cycle finished in {elapsed:.1f}s (rc={rc}) ════════════")
    return rc


if __name__ == "__main__":
    sys.exit(main())
