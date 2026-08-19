"""Nuclear Intelligence Space presentation layer.

This module intentionally contains no research engine, safety policy, evaluator,
ledger or autonomous-loop implementation. It renders the canonical runtime
through ``core_hf.HeadlessHFAdapter``.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, Iterable, List

import gradio as gr
import pandas as pd
import plotly.express as px

from core_hf import get_adapter


APP_VERSION = "6.2.0"
PUBLIC_CYCLE_ENABLED = os.getenv("PUBLIC_CYCLE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
PUBLIC_DATASET_WRITE_ENABLED = os.getenv("PUBLIC_DATASET_WRITE_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
SPACE_AUTONOMY_ENABLED = os.getenv("SPACE_AUTONOMY_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
SPACE_AUTONOMY_INTERVAL_SECONDS = max(900, int(os.getenv("SPACE_AUTONOMY_INTERVAL_SECONDS", "1800")))
EMERGENCY_STOP = os.getenv("EMERGENCY_STOP", "false").strip().lower() in {"1", "true", "yes", "on"}


def _adapter():
    return get_adapter()


_worker_stop = threading.Event()
_worker_thread: threading.Thread | None = None


def _autonomous_worker() -> None:
    """Run bounded governed cycles inside the live Space process."""
    if not SPACE_AUTONOMY_ENABLED or EMERGENCY_STOP:
        return
    while not _worker_stop.is_set():
        try:
            result = _adapter().run_cycle(dev_mode=False, public=False)
            if result.get("minted") and os.getenv("SYNC_TO_HF", "true").lower() in {"1", "true", "yes", "on"}:
                _adapter().sync_to_hf_dataset(result)
        except Exception:
            # The UI must remain available even when a provider or sync is down.
            pass
        _worker_stop.wait(SPACE_AUTONOMY_INTERVAL_SECONDS)


def start_autonomous_worker() -> None:
    global _worker_thread
    if _worker_thread is None and SPACE_AUTONOMY_ENABLED and not EMERGENCY_STOP:
        _worker_thread = threading.Thread(target=_autonomous_worker, name="ni-space-autonomy", daemon=True)
        _worker_thread.start()


def _safe_mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _markdown_error(payload: Dict[str, Any]) -> str:
    return f"## ⚠️ Runtime unavailable\n\n`{payload.get('error', 'unknown error')}`"


def overview_markdown() -> str:
    stats = _adapter().system_stats()
    if stats.get("error"):
        return _markdown_error(stats)
    core = _safe_mapping(stats.get("core"))
    loop = _safe_mapping(stats.get("loop"))
    ledger = _safe_mapping(stats.get("ledger"))
    runtime = _safe_mapping(stats.get("runtime"))
    return f"""## Operational overview

| Signal | Current value |
|---|---:|
| Runtime | `canonical shared core` |
| Providers available | {len(runtime.get('providers', []))} |
| Research cycles | {loop.get('total_cycles', core.get('researches_conducted', 0)):,} |
| Accepted knowledge | {loop.get('tokens_minted', core.get('tokens_minted', 0)):,} |
| Rejected output | {loop.get('tokens_rejected', core.get('tokens_rejected', 0)):,} |
| Knowledge entities | {core.get('knowledge_entities', 0):,} |
| Ledger valid | {'✅' if ledger.get('chain_valid', ledger.get('valid', False)) else '⚠️'} |
| NES supply | {ledger.get('nes_supply', 0):,.1f} |

The Space is a presentation layer over the same canonical runtime used by GitHub automation and API services. Every accepted knowledge item remains subject to safety, evidence, consistency and provenance gates."""


def provider_markdown() -> str:
    status = _adapter().public_status()
    if not status.get("ready"):
        return _markdown_error(status)
    providers = status.get("providers", [])
    return "## Runtime diagnostics\n\n" + "\n".join([
        f"- **State:** {'✅ ready' if status.get('ready') else '⚠️ initializing'}",
        f"- **Providers:** `{', '.join(providers) if providers else 'none configured'}`",
        f"- **Repository sync:** Hugging Face `{status.get('sync', {}).get('huggingface', False)}` · GitHub `{status.get('sync', {}).get('github', False)}`",
        f"- **Evaluation samples:** `{status.get('thresholds', {}).get('evaluation_samples', 1)}`",
        f"- **Agreement threshold:** `{status.get('thresholds', {}).get('evaluation_agreement_threshold', 'N/A')}`",
    ])


def governance_markdown() -> str:
    governance = _adapter().governance()
    if governance.get("error"):
        return _markdown_error(governance)
    admission = _safe_mapping(governance.get("admission"))
    return f"""## Research governance

| Signal | Count |
|---|---:|
| Cycles observed | {governance.get('cycles_observed', 0):,} |
| Evidence-gate approved | {admission.get('approved', 0):,} |
| Evidence-gate rejected | {admission.get('rejected', 0):,} |
| Legacy / unavailable decision records | {admission.get('unavailable', 0):,} |
| Open review-required proposals | {len(governance.get('open_proposals', [])):,} |

The controller selects under-covered civilian-energy areas and can only **tighten** the admission gate. Proposals are advisory and review-required; the Space cannot change code, safety policy, secrets, external accounts or real-world transactions."""


def category_figure():
    governance = _adapter().governance()
    coverage = _safe_mapping(governance.get("category_coverage"))
    if not coverage:
        return px.bar(title="No category coverage recorded yet")
    data = pd.DataFrame(sorted(coverage.items()), columns=["Category", "Research cycles"])
    fig = px.bar(data, x="Category", y="Research cycles", color="Research cycles", color_continuous_scale="Teal")
    fig.update_layout(height=330, margin=dict(l=20, r=20, t=35, b=70), coloraxis_showscale=False)
    return fig


def governance_tables():
    governance = _adapter().governance()
    coverage = _safe_mapping(governance.get("category_coverage"))
    coverage_df = pd.DataFrame(
        [{"Category": category, "Cycles": count} for category, count in sorted(coverage.items())]
        or [{"Category": "No data", "Cycles": 0}]
    )
    proposals = governance.get("open_proposals", []) if isinstance(governance, dict) else []
    proposal_df = pd.DataFrame(proposals or [{"title": "No open review-required proposals", "status": "—"}])
    return coverage_df, proposal_df


def cycle_table():
    cycles = _adapter().recent_cycles(30)
    rows: List[Dict[str, Any]] = []
    for cycle in cycles:
        question = _safe_mapping(cycle.get("question"))
        evaluation = _safe_mapping(cycle.get("evaluation"))
        governance = _safe_mapping(cycle.get("governance"))
        admission = _safe_mapping(governance.get("admission"))
        rows.append({
            "Time": str(cycle.get("timestamp", ""))[:19],
            "Category": question.get("category", "N/A"),
            "Outcome": "Accepted" if cycle.get("minted") else "Rejected",
            "Accuracy": round(float(evaluation.get("scientific_accuracy", 0) or 0), 1),
            "Novelty": round(float(evaluation.get("novelty_score", 0) or 0), 1),
            "Evidence gate": "Passed" if admission.get("approved") else "Blocked",
            "Provider": _safe_mapping(cycle.get("answer")).get("provider", "N/A"),
        })
    return pd.DataFrame(rows or [{"Time": "No cycles", "Category": "—", "Outcome": "—", "Accuracy": 0, "Novelty": 0, "Evidence gate": "—", "Provider": "—"}])


def research_cycle(dev_mode: bool, sync_dataset: bool):
    result = _adapter().run_cycle(dev_mode=False, public=True)
    if result.get("error"):
        return _markdown_error(result), governance_markdown(), cycle_table()
    evaluation = _safe_mapping(result.get("evaluation"))
    governance = _safe_mapping(result.get("governance"))
    admission = _safe_mapping(governance.get("admission"))
    question = _safe_mapping(result.get("question"))
    answer = _safe_mapping(result.get("answer"))
    state = "✅ ACCEPTED" if result.get("minted") else "⛔ REJECTED"
    sync_note = ""
    if sync_dataset and PUBLIC_DATASET_WRITE_ENABLED and result.get("minted"):
        sync_note = f"\n\n**Dataset publication:** {'✅ completed' if _adapter().sync_to_hf_dataset(result) else '⚠️ unavailable or skipped'}"
    response = f"""## {state}

**Agenda:** `{_safe_mapping(governance.get('agenda')).get('selected_category', question.get('category', 'N/A'))}`  
**Question:** {question.get('question', 'N/A')}  
**Provider:** `{answer.get('provider', 'N/A')}`  
**Evidence gate:** `{'passed' if admission.get('approved') else 'blocked'}`

| Dimension | Score |
|---|---:|
| Scientific accuracy | {float(evaluation.get('scientific_accuracy', 0) or 0):.1f}% |
| Novelty | {float(evaluation.get('novelty_score', 0) or 0):.1f}% |
| Usefulness | {float(evaluation.get('usefulness_score', 0) or 0):.1f}% |
| Completeness | {float(evaluation.get('completeness', 0) or 0):.1f}% |

**Decision reasons:** {'; '.join(admission.get('reasons', [])[:5]) or 'recorded in the cycle report'}{sync_note}"""
    return response, governance_markdown(), cycle_table()


def manual_research(question: str, developer_mode: bool):
    result = _adapter().ask_question(question, developer_mode=False)
    if result.get("error"):
        return _markdown_error(result)
    if result.get("refused"):
        return result.get("message", "## 🛡️ Request refused by the safety policy")
    evaluation = _safe_mapping(result.get("evaluation"))
    citations = result.get("citations", []) or []
    citation_text = "\n".join(f"- {citation}" for citation in citations[:8]) or "- No citations returned"
    return f"""## Research answer

**Provider:** `{result.get('provider', 'N/A')}`

{result.get('answer', '')}

### Quality

| Dimension | Score |
|---|---:|
| Scientific accuracy | {float(evaluation.get('scientific_accuracy', 0) or 0):.1f}% |
| Novelty | {float(evaluation.get('novelty_score', 0) or 0):.1f}% |
| Usefulness | {float(evaluation.get('usefulness_score', 0) or 0):.1f}% |
| Completeness | {float(evaluation.get('completeness', 0) or 0):.1f}% |

### Sources
{citation_text}"""


def knowledge_search(query: str, limit: int):
    results = _adapter().knowledge_search(query, limit)
    if not results:
        return "## Knowledge search\n\nNo matching evidence was found.", pd.DataFrame([{"Question": "No matches", "Category": "—", "Accuracy": 0, "Similarity": 0}])
    rows, blocks = [], ["## Knowledge search"]
    for index, item in enumerate(results, start=1):
        metadata = _safe_mapping(item.get("metadata"))
        rows.append({
            "Question": str(item.get("question", ""))[:180],
            "Category": metadata.get("category", "N/A"),
            "Accuracy": metadata.get("accuracy", 0),
            "Similarity": item.get("_score", 0),
        })
        blocks.append(f"### {index}. {item.get('question', '')[:180]}\n**Category:** `{metadata.get('category', 'N/A')}` · **Accuracy:** `{metadata.get('accuracy', 0):.0f}`")
    return "\n\n".join(blocks), pd.DataFrame(rows)


def ledger_markdown() -> str:
    status = _adapter().ledger_status()
    if status.get("error"):
        return _markdown_error(status)
    return f"""## Ledger integrity

| Signal | Value |
|---|---:|
| Status | {'✅ valid' if status.get('valid') or status.get('chain_valid') else '⚠️ requires review'} |
| Chain length | {status.get('chain_length', 0):,} |
| Transactions | {status.get('total_transactions', 0):,} |
| NES supply | {status.get('nes_supply', 0):,.1f} |
| Blocks mined | {status.get('blocks_mined', 0):,} |
| Mining time | {status.get('total_mining_time', 'N/A')} |
"""


def export_json():
    return _adapter().export_state(25)


CSS = """
.gradio-container { max-width: 1440px !important; }
#hero { text-align:center; padding: 16px 0 6px; }
#hero h1 { font-size: 2.6rem; margin-bottom: .35rem; }
.metric-note { color: #6b7280; }
"""

with gr.Blocks(title="Nuclear Intelligence", theme=gr.themes.Soft(primary_hue="cyan"), css=CSS) as demo:
    gr.Markdown(
        "# ⚛️ Nuclear Intelligence", elem_id="hero"
    )
    gr.Markdown(
        "**Evidence-led civilian nuclear-energy research with independent quality gates, auditable governance and a shared canonical runtime.**"
    )

    with gr.Row():
        with gr.Column(scale=3):
            overview = gr.Markdown(overview_markdown)
        with gr.Column(scale=1):
            refresh_overview = gr.Button("Refresh overview", variant="secondary")
            runtime_box = gr.Markdown(provider_markdown)

    with gr.Tabs():
        with gr.Tab("Research"):
            with gr.Row():
                run_button = gr.Button("Run governed research cycle", variant="primary", interactive=PUBLIC_CYCLE_ENABLED)
                developer_mode = gr.Checkbox(label="Include development analysis (operator-only)", value=False, visible=False, interactive=False)
                sync_dataset = gr.Checkbox(label="Publish accepted report to dataset (operator-only)", value=False, visible=PUBLIC_DATASET_WRITE_ENABLED, interactive=PUBLIC_DATASET_WRITE_ENABLED)
            cycle_output = gr.Markdown("A governed cycle selects a peaceful-use topic, researches it and applies evidence gates before acceptance.")
            with gr.Accordion("Manual research", open=False):
                manual_question = gr.Textbox(label="Research question", placeholder="How can passive safety improve small modular reactor resilience?", lines=3)
                manual_dev = gr.Checkbox(label="Include development analysis (operator-only)", value=False, visible=False, interactive=False)
                manual_button = gr.Button("Research this question")
                manual_output = gr.Markdown()

        with gr.Tab("Evidence & knowledge"):
            with gr.Row():
                search_box = gr.Textbox(label="Search the knowledge graph", placeholder="fusion, passive safety, waste management")
                search_limit = gr.Slider(label="Results", minimum=1, maximum=25, value=10, step=1)
                search_button = gr.Button("Search")
            search_output = gr.Markdown()
            search_table = gr.Dataframe(headers=["Question", "Category", "Accuracy", "Similarity"], interactive=False)

        with gr.Tab("Governance"):
            governance_output = gr.Markdown(governance_markdown)
            with gr.Row():
                coverage_plot = gr.Plot(category_figure)
                coverage_table = gr.Dataframe(headers=["Category", "Cycles"], interactive=False)
            gr.Markdown("### Review-required development proposals")
            proposals_table = gr.Dataframe(interactive=False)
            refresh_governance = gr.Button("Refresh governance")

        with gr.Tab("Quality history"):
            gr.Markdown("### Recent governed cycles")
            recent_cycles = gr.Dataframe(interactive=False)
            refresh_cycles = gr.Button("Refresh history")

        with gr.Tab("Ledger & export"):
            ledger_output = gr.Markdown(ledger_markdown)
            refresh_ledger = gr.Button("Verify ledger")
            export_button = gr.Button("Prepare safe state export")
            export_output = gr.JSON(label="Portable, non-secret runtime state")

    def refresh_governance_view():
        coverage, proposals = governance_tables()
        return governance_markdown(), category_figure(), coverage, proposals

    refresh_overview.click(lambda: (overview_markdown(), provider_markdown()), outputs=[overview, runtime_box])
    run_button.click(research_cycle, inputs=[developer_mode, sync_dataset], outputs=[cycle_output, governance_output, recent_cycles])
    manual_button.click(manual_research, inputs=[manual_question, manual_dev], outputs=manual_output)
    search_button.click(knowledge_search, inputs=[search_box, search_limit], outputs=[search_output, search_table])
    refresh_governance.click(refresh_governance_view, outputs=[governance_output, coverage_plot, coverage_table, proposals_table])
    refresh_cycles.click(cycle_table, outputs=recent_cycles)
    refresh_ledger.click(ledger_markdown, outputs=ledger_output)
    export_button.click(export_json, outputs=export_output)
    demo.load(refresh_governance_view, outputs=[governance_output, coverage_plot, coverage_table, proposals_table])
    demo.load(cycle_table, outputs=recent_cycles)


if __name__ == "__main__":
    start_autonomous_worker()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_PORT", "7860")))
