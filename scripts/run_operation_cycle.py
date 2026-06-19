#!/usr/bin/env python3
"""
Nuclear Intelligence - Run Operation Cycle (Self-contained)
Uses the lightweight HF-deploy compatible core for fast, reliable cycles.
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "hf_deploy"))


def run_cycle():
    """Run a single research cycle using the HF-deploy compatible core."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hf_app",
        str(Path(__file__).parent.parent / "hf_deploy" / "app.py"),
    )
    hf_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hf_app)

    core = hf_app.core
    if not core:
        print("❌ Core not initialized")
        return 1

    print("══════════════════════════════════════")
    print("⚛️  Nuclear Intelligence v4.0 - Research Cycle")
    print("══════════════════════════════════════")
    print(f"Providers: {core.llm._available}")
    print(f"Current NES supply: {core.ledger.nes_supply}")
    print()

    # Run cycle
    result = core.run_cycle(dev_mode=True)

    status = "✅ MINTED" if result["minted"] else "❌ REJECTED"
    print(f"\n{'='*50}")
    print(f"CYCLE RESULT: {status}")
    print(f"{'='*50}")
    print(f"Cycle ID:    {result['cycle_id']}")
    print(f"Provider:    {result['research']['provider']}")
    print(f"Time:        {result['execution_time_seconds']}s")
    print()
    print("Question:")
    print(f"  [{result['question']['category']}] {result['question']['question']}")
    print()
    print("Scores:")
    eval_data = result["evaluation"]
    print(f"  Accuracy:    {eval_data['scientific_accuracy']:.1f}%")
    print(f"  Novelty:     {eval_data['novelty_score']:.1f}%")
    print(f"  Usefulness:  {eval_data['usefulness_score']:.1f}%")
    print(f"  Completeness:{eval_data['completeness']:.1f}%")
    print(f"  Overall:     {result['overall']:.1f}%")
    print()
    if result.get("tx_hash"):
        print(f"TX Hash:     {result['tx_hash'][:40]}...")
        print(f"NES Minted:  +100.0 (total: {core.ledger.nes_supply})")
    print(f"{'='*50}\n")

    # Save report
    os.makedirs("reports", exist_ok=True)
    prefix = "cycle_minted" if result["minted"] else "cycle_rejected"
    report_file = f"reports/{prefix}_{result['cycle_id']}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"📄 Report saved: {report_file}")

    return 0 if result["minted"] else 0


if __name__ == "__main__":
    sys.exit(run_cycle())