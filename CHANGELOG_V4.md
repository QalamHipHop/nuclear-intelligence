# ⚛️ Nuclear Intelligence v4.0 — Changelog

> **Date:** 2026-06-19
> **Scope:** Hardening, safety, evaluation, RAG, i18n, ops

This release hardens the production pipeline with a **defensive safety
layer**, **multi-layer evaluation**, **RAG quality boosting**, and
**multilingual (English + Persian/Farsi)** support. All changes are
*additive* — existing callers keep working.

---

## 🛡️ New: Safety & Ethics Guardrails (`core/safety_guard.py`)

A *hard* pre-LLM and post-generation filter that enforces:

- **No assistance** with weapons design, fabrication, or use
- **No actionable details** on prohibited enrichment / weapons-usable
  material / illicit trafficking / radiological dispersal devices
- **No cyber-proliferation** guidance for nuclear facilities
- **Compliance** with NPT, IAEA safeguards, NSG, Zangger, PSI norms
- **Redirection** to legitimate peaceful-use topics when refused

### Coverage

| Category | Example refused phrase | Redirected to |
|---|---|---|
| `weapon_design` | "how to build a nuclear bomb" | NPT/CTBT history & verification |
| `enrichment_prohibited` | "clandestine enrichment centrifuge" | IAEA-monitored civilian enrichment |
| `weapons_material` | "reprocess plutonium for weapons" | MOX, civilian Pu disposition |
| `illicit_trafficking` | "smuggling HEU" | NSG / Zangger / PSI regimes |
| `weaponization_tips` | "implosion lens design equation" | Stockpile stewardship & safety |
| `radiological_dispersal` | "build a dirty bomb with Cs-137" | Radiation protection & CBRN security |
| `cyber_proliferation` | "Stuxnet-like attack instructions" | IEC 62443 for nuclear I&C |

### Verification

19/19 safety unit tests pass. Includes both **input filter** (refuse
before the LLM ever sees the prompt) and **output filter** (catch
weaponization leakage in the generated answer).

---

## 📊 New: Enhanced Evaluation (`core/evaluation_enhanced.py`)

Adds three new layers on top of the existing single-pass LLM-as-judge:

### 1. Self-Consistency (`ConsistencyReport`)
- Generate N independent evaluations, take the median per dimension
- `agreement = 1 − mean(coeff_of_variation)` across dimensions
- Bonus if `agreement ≥ 0.80`

### 2. Citation Quality (`CitationQuality`)
- Counts inline citations `[1]`, `(2024)`, `et al.`
- Trusted-source ratio (IAEA, NRC, DOE labs, peer-reviewed)
- DOI / year detection
- Penalty for vague promotional phrases
  (`"broadly speaking"`, `"some experts say"`, …)

### 3. Novelty vs Knowledge Graph
- 3-gram Jaccard distance against existing KG entities
- Maps similarity → novelty (50–100)

### 4. Tokenization-Readiness composite (`TokenizationReadiness`)
- Weighted blend: `accuracy 0.40 / novelty 0.20 / usefulness 0.20 /
  self_consistency 0.10 / citation_quality 0.10`
- Canonical thresholds: **Accuracy ≥ 93 %, Novelty ≥ 75 %,
  Usefulness ≥ 80 %, Self-Consistency ≥ 0.80, Citation-Quality ≥ 50**,
  **Overall ≥ 85 %**
- Returns a binary `ready_to_mint` flag + per-dimension notes

---

## 📚 New: Enhanced RAG (`core/rag_enhanced.py`)

Layered on top of `WebSearchEngine`:

- **Domain weighting** (IAEA 2.5×, NRC 2.5×, DOE labs 2.0×,
  peer-reviewed 1.7–1.8×, Wikipedia 0.9×, blog 1.0×)
- **Recency boost** for hits with a recent year mention
- **Re-ranking** combines query overlap + domain + recency
- **Source diversification** round-robins across hosts so the top-K
  hits aren't all from one source
- **Context builder** + **stats summary** for the UI

---

## 🌐 New: Multilingual (i18n) — `core/i18n.py`

- **Language detection**: counts Perso-Arabic letters; > 20 % ⇒ `fa`
- **Localized UI labels** (research_label, accuracy_label, …)
- **Persian system prompt fragment** for the LLM
- Falls back to English for any non-Persian input

Tested: 5/5 detection cases pass; Persian labels render correctly.

---

## 🔒 Security: Hardcoded Key Removal

Removed hardcoded `AIMLAPI_API_KEY = "bd510ec538561ec582dc003b6070cf6d"`
from:

- `app.py` (line 30)
- `core/llm_engine_v4.py` (line 188)
- `core/llm_engine.py` (line 268)

All keys now flow through `.env` / `os.environ` only. Operators are
**strongly advised** to rotate the previously-exposed key.

---

## 🩺 New: Health & Self-Test — `scripts/health_check.py`

Run anytime:

```bash
python scripts/health_check.py
```

Smoke-tests every module that doesn't require live LLM credentials:

```
🩺 Nuclear Intelligence v4.0 — Health Check

── Safety ──
  ✅ safety.query_filter (refused 1 phrases)
  ✅ safety.output_filter (blocked 1 leak)
── Evaluation ──
  ✅ eval.scoring (overall=85.7, ready=False)
── RAG ──
  ✅ rag.rerank_diversity (iaea_w=2.5, ctx_len=141)
── i18n ──
  ✅ i18n.detect_translate (fa=fa, en=en)
── Storage ──
  ✅ storage.kg_roundtrip (entities=1)
  ✅ storage.ledger (chain_len=1, valid=True)
── Core ──
  ✅ core.embeddings (engine loaded)
  ✅ core.llm_engine_static (providers=7, lru_ok)
=== 9/9 checks passed ===
```

Wired into the Gradio UI under **🛡️ Safety & Health → 🩺 Pipeline
Health Check** tab.

---

## 🖥️ Gradio UI Additions

- **New tab: 🛡️ Safety & Health** with:
  - Interactive safety-prompt tester (paste any prompt → see if it's
    allowed / refused + matched phrases + redirect topic)
  - One-click **Run Self-Test** that invokes `scripts/health_check.py`
    and shows full output
- **`ask_question()` upgraded** to:
  - Detect dangerous prompts up front (never reaches the LLM)
  - Run output filter on the generated answer
  - Compute **Citation Quality** + **Tokenization-Readiness Score**
  - Switch UI labels to Persian when input is Persian

---

## 🚀 Migration Notes

- **Backward compatible.** Existing callers of `EvaluationScore`,
  `OperationLoop`, `NuclearIntelligenceCore` see no breaking changes.
- New modules are *opt-in*: import them where you want the upgrade.
- Hardcoded-key removal means you must now set `AIMLAPI_API_KEY`
  in `.env` (see `.env.template`).

---

## 📁 Files Changed

| File | Status | Notes |
|---|---|---|
| `core/safety_guard.py` | **NEW** | Weapons / proliferation / RDD filters |
| `core/evaluation_enhanced.py` | **NEW** | Self-consistency + citation + readiness |
| `core/rag_enhanced.py` | **NEW** | Domain-weighted re-ranking + diversity |
| `core/i18n.py` | **NEW** | Persian / English detection + labels |
| `scripts/health_check.py` | **NEW** | Self-test runner (9 checks) |
| `app.py` | UPDATED | Safety + i18n + readiness + new tab |
| `hf_deploy/app.py` | UPDATED | Inline defensive safety wrapper |
| `core/llm_engine_v4.py` | SECURITY | Removed hardcoded key |
| `core/llm_engine.py` | SECURITY | Removed hardcoded key |
| `CHANGELOG_V4.md` | **NEW** | This file |

---

*Developed by **Qalam** · License: MIT · NES Token Standard v3.0*
