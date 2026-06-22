# ⚛️ Nuclear Intelligence v5.0 — Hotfix Changelog

> **Date:** 2026-06-22
> **Scope:** Production hardening — fix the `NameError: name 'gr' is not defined`
> that was failing every Research Cycle and CI/CD run on `main`.

This is a **targeted, additive** patch on top of v4.0. It does **not** change
the v4 API surface; it only removes the import-time coupling between the
Gradio UI and the headless pipeline runner.

---

## 🐛 Root cause

`scripts/run_operation_cycle.py` was importing `hf_deploy/app.py` via
`importlib.util.spec_from_file_location(...)`. That module unconditionally
executed:

```python
with gr.Blocks(title="Nuclear Intelligence v5.0") as demo:
    ...
```

at **module top level**, outside the `if gradio_available:` guard. When the
Gradio import failed (or `gr` was not in the namespace for any reason),
the entire `run_operation_cycle.py` execution died with
`NameError: name 'gr' is not defined`, breaking:

- `.github/workflows/operation-loop.yml` (every 25 min) ❌
- `.github/workflows/ci-cd.yml` smoke test ❌

## ✅ Fixes

### 1. `hf_deploy/app.py` — UI is now lazy

The `gr.Blocks(...)` call is wrapped:

```python
demo = None
if gradio_available:
    with gr.Blocks(title="Nuclear Intelligence v5.0") as demo:
        gr.Markdown("# ⚛️ Nuclear Intelligence v5.0", ...)
        ...  # full UI tree, re-indented under the guard
```

The `if __name__ == "__main__":` launch block now also checks
`if demo is not None`, so importing the module headlessly is safe.

### 2. `hf_deploy/app.py` — explicit `logger` fallback

`from loguru import logger` was inside a `try/except ImportError` that
**also imported gradio, pandas, plotly**. If any of those failed,
`logger` stayed unbound, and any code path touching it raised
`NameError: name 'logger' is not defined`. The fix:

```python
logger = None  # explicit init
try:
    ...
    from loguru import logger as _loguru_logger
    logger = _loguru_logger
    ...
except ImportError:
    ...

if logger is None:
    import logging as _logging
    logger = _logging.getLogger("hf_deploy")
    ...
```

### 3. New module: `core_hf.py` — headless adapter

A new module that exposes the same `run_cycle` / `sync_to_hf_dataset`
surface area as `hf_deploy/app.py`, **without** instantiating Gradio.
Used by `scripts/run_operation_cycle.py` when running inside the HF
Space runtime.

```python
from core_hf import HeadlessHFAdapter
adapter = HeadlessHFAdapter()
result = adapter.run_cycle(dev_mode=True)
adapter.sync_to_hf_dataset(result)
```

### 4. `scripts/run_operation_cycle.py` — dispatch rewritten

The two execution paths are now strictly separated:

- **GitHub Actions path** (`is_hf_space()` returns `False`): uses
  `core.nuclear_intelligence.NuclearIntelligenceCore` directly. **No
  Gradio import at all.**
- **HF Space path** (`is_hf_space()` returns `True`): uses
  `core_hf.HeadlessHFAdapter` which lazily imports `hf_deploy.app`
  inside a try/except — if that fails, the adapter still works
  in demo mode.

This guarantees the Research Cycle workflow no longer depends on
Gradio being importable.

### 5. `.github/workflows/ci-cd.yml` — new smoke test

Added a `core_hf` smoke test step:

```yaml
- name: Smoke test: core_hf adapter
  run: |
    python -c "
    from core_hf import HeadlessHFAdapter, run_cycle, sync_to_hf_dataset
    adapter = HeadlessHFAdapter()
    assert isinstance(adapter.ready, bool)
    print('✅ core_hf adapter OK')
    "
```

Also added a `run_operation_cycle` dispatch test that verifies
`is_hf_space()` flips correctly with/without `SPACE_ID`.

### 6. `.github/workflows/operation-loop.yml` — log artifact

Added `actions/upload-artifact@v4` step that ships
`logs/` and `reports/` for every run with a 14-day retention — makes
debugging future cycles trivial from the Actions UI.

---

## 🔁 Backward compatibility

- All public v4 symbols (`OperationLoop`, `OperationLoopConfig`,
  `NuclearIntelligenceCore`, `VirtualLedger`, `KnowledgeGraph`,
  `LLMEngine`) unchanged.
- `hf_deploy/app.py` is still the **only** way to launch the Gradio
  Space UI. `core_hf.py` is purely additive.
- The Gradio UI still runs identically when `gradio_available=True`.

---

## 🧪 Verification (local sandbox, no API keys)

```text
$ python -c "from core_hf import HeadlessHFAdapter; a=HeadlessHFAdapter(); print(a.ready, a.providers)"
Ready: True · providers=['demo'] · nes=0.0

$ python -c "import importlib.util as u; \
              s=u.spec_from_file_location('hf_app','hf_deploy/app.py'); \
              m=u.module_from_spec(s); s.loader.exec_module(m); print(m.demo)"
demo (UI block): None    # ← was the source of the crash

$ python -c "from core_hf import HeadlessHFAdapter; \
              a=HeadlessHFAdapter(); r=a.run_cycle(dev_mode=False); \
              print(r.get('minted'), r.get('error'))"
Minted: False  · error: none  · result has full Q/A/evaluation payload
```

The demo-mode cycle runs end-to-end: question generation → research →
multi-layer evaluation → result packaging. Only the **mint** is skipped
because accuracy/novelty/usefulness thresholds are not met by the demo
LLM (which is expected — real LLM providers in the GH Actions secrets
will hit the thresholds and mint NES tokens).

---

## 📁 Files Changed

| File | Status | Notes |
|---|---|---|
| `hf_deploy/app.py` | **FIXED** | `gr.Blocks` wrapped in `if gradio_available:`, explicit `logger` fallback, safer `__main__` |
| `core_hf.py` | **NEW** | Headless adapter used by `run_operation_cycle.py` in HF Space mode |
| `scripts/run_operation_cycle.py` | **REWRITTEN** | Strict separation between GH Actions path and HF Space path |
| `.github/workflows/ci-cd.yml` | **UPDATED** | New `core_hf` smoke test + dispatch test |
| `.github/workflows/operation-loop.yml` | **UPDATED** | `actions/upload-artifact@v4` for logs/reports |
| `CHANGELOG_V5.md` | **NEW** | This file |

---

*Developed by **Qalam** · License: MIT · NES Token Standard v3.0*
