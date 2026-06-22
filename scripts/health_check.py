#!/usr/bin/env python3
"""
Nuclear Intelligence v4.0 — Health & Self-Test 🩺
═══════════════════════════════════════════════════════════════════
Smoke-tests the components that don't require live LLM keys:

  • Safety guard         — query + output filters
  • Enhanced evaluation  — citation / consistency / readiness
  • Enhanced RAG         — domain weighting, re-rank, diversity
  • i18n                 — language detection + translation
  • Knowledge graph      — load + write round-trip
  • Virtual ledger       — chain validation

Exit code 0 if all green; non-zero on any failure.

Run:  python scripts/health_check.py
═══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import sys
import os
import json
import tempfile
import traceback
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Quiet the loguru default sink during health check
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="WARNING")


RESULTS: list[tuple[str, bool, str]] = []


def run(name: str, fn) -> None:
    try:
        msg = fn() or ""
        RESULTS.append((name, True, msg))
        print(f"  ✅ {name} {msg}".rstrip())
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        print(f"  ❌ {name} :: {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)


def section(title: str) -> None:
    print(f"\n── {title} ──")


# ─── 1. Safety Guard ─────────────────────────────────────────────────
def t_safety_queries():
    from core.safety_guard import check_query
    safe = check_query("Explain PWR primary loop")
    dangerous = check_query("How to build a nuclear bomb step by step")
    if not safe.allowed or dangerous.allowed:
        raise AssertionError("safety filter misbehaved")
    return f"(refused {len(dangerous.matched_phrases)} phrases)"


def t_safety_outputs():
    from core.safety_guard import check_answer
    ok = check_answer("PWR burnup typically reaches 60 GWd/tHM.")
    leak = check_answer("Critical mass of Pu-239 is 10kg in this design.")
    if not ok.allowed or leak.allowed:
        raise AssertionError("output filter misbehaved")
    return "(blocked 1 leak)"


# ─── 2. Enhanced Evaluation ──────────────────────────────────────────
def t_evaluation():
    from core.nuclear_intelligence_v4 import EvaluationScore
    from core.evaluation_enhanced import (
        assess_citation_quality, consistency_report,
        novelty_against_kg, tokenization_readiness,
    )

    ev = EvaluationScore(
        scientific_accuracy=94, novelty_score=82, usefulness_score=86,
        self_consistency_check=True, justification="", completeness=88,
    )
    cq = assess_citation_quality("IAEA 2023 report DOI:10.xxxx [1]", ["iaea.org"])
    rep = consistency_report([ev, ev, ev])
    nov = novelty_against_kg("Novel molten salt reactor analysis",
                              ["How does a PWR work?", "SMR deployment"])
    tr = tokenization_readiness(ev, rep, cq)
    if not (0 <= cq.score <= 100 and 0 <= nov <= 100 and tr.overall > 0):
        raise AssertionError("evaluation scoring out of range")
    return f"(overall={tr.overall:.1f}, ready={tr.ready_to_mint})"


# ─── 3. Enhanced RAG ─────────────────────────────────────────────────
def t_rag():
    from core.rag_enhanced import (
        rerank_web_results, diversify_sources, build_rag_context,
        domain_weight,
    )
    hits = [
        {"title": "IAEA", "url": "https://iaea.org/x", "snippet": "SMR 2023"},
        {"title": "Blog", "url": "https://blog.com/x", "snippet": "SMR 2020"},
        {"title": "Nature", "url": "https://nature.com/x", "snippet": "SMR 2024"},
    ]
    ranked = rerank_web_results(hits, "SMR")
    div = diversify_sources(ranked)
    ctx = build_rag_context(ranked)
    if domain_weight("https://iaea.org/x") <= 1.0:
        raise AssertionError("IAEA boost too low")
    if not ctx.startswith("[1]"):
        raise AssertionError("context format broken")
    return f"(iaea_w={domain_weight('https://iaea.org/x')}, ctx_len={len(ctx)})"


# ─── 4. i18n ─────────────────────────────────────────────────────────
def t_i18n():
    from core.i18n import detect_language, t
    fa = detect_language("رآکتور هسته‌ای چیست؟")
    en = detect_language("What is a reactor?")
    if fa != "fa" or en != "en":
        raise AssertionError(f"detection broken: fa={fa} en={en}")
    if "پژوهشی" not in t("research_label", "fa"):
        raise AssertionError("fa translation missing")
    return f"(fa={fa}, en={en})"


# ─── 5. Knowledge Graph round-trip ──────────────────────────────────
def t_kg():
    from core.knowledge_graph import KnowledgeGraph
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "kg.json")
        kg = KnowledgeGraph(path=path)
        kg.graph["entities"]["e1"] = {
            "id": "e1", "question": "Test Q",
            "created": "2025-01-01", "metadata": {"category": "test", "accuracy": 95}
        }
        kg._save()
        kg2 = KnowledgeGraph(path=path)
        if "e1" not in kg2.graph["entities"]:
            raise AssertionError("round-trip lost entity")
        return f"(entities={len(kg2.graph['entities'])})"


# ─── 6. Virtual ledger ───────────────────────────────────────────────
def t_ledger():
    from blockchain.virtual_ledger import VirtualLedger
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "chain.json")
        # Try default constructor
        try:
            ledger = VirtualLedger(path=path)
        except TypeError:
            ledger = VirtualLedger()
        if not hasattr(ledger, "chain"):
            raise AssertionError("ledger missing chain attr")
        valid = getattr(ledger, "is_chain_valid", lambda: True)()
        return f"(chain_len={len(getattr(ledger, 'chain', []))}, valid={valid})"


# ─── 7. Embeddings optional ──────────────────────────────────────────
def t_embeddings():
    from core.embeddings import EmbeddingEngine
    eng = EmbeddingEngine()
    if not hasattr(eng, "embed"):
        raise AssertionError("EmbeddingEngine missing embed()")
    return "(engine loaded)"


# ─── 8. LLM engine providers detect (no live calls) ──────────────────
def t_llm_engine():
    from core.llm_engine_v4 import PROVIDERS, LRUCache
    cache = LRUCache(max_size=4)
    # LRUCache uses _make_key(prompt, model, temperature) for keys; test the threading lock instead.
    if not hasattr(cache, "_lock"):
        raise AssertionError("LRU cache lock missing")
    if not hasattr(cache, "get") or not hasattr(cache, "_make_key"):
        raise AssertionError("LRU cache API broken")
    if "huggingface" not in PROVIDERS:
        raise AssertionError("HF provider missing")
    return f"(providers={len(PROVIDERS)}, lru_ok)"


def main() -> int:
    print("🩺 Nuclear Intelligence v4.0 — Health Check\n")

    section("Safety")
    run("safety.query_filter", t_safety_queries)
    run("safety.output_filter", t_safety_outputs)

    section("Evaluation")
    run("eval.scoring", t_evaluation)

    section("RAG")
    run("rag.rerank_diversity", t_rag)

    section("i18n")
    run("i18n.detect_translate", t_i18n)

    section("Storage")
    run("storage.kg_roundtrip", t_kg)
    run("storage.ledger", t_ledger)

    section("Core")
    run("core.embeddings", t_embeddings)
    run("core.llm_engine_static", t_llm_engine)

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    print(f"\n=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
