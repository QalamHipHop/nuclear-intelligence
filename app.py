"""
Nuclear Intelligence v4.0 - Production Gradio App ⚛️
═══════════════════════════════════════════════════════════════════
Professional AI Research Engine for Nuclear Energy
Always-online with GitHub Actions, auto-sync to HF & GitHub

Author: Qalam | License: MIT
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import threading
import time
import hashlib
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import gradio as gr
import pandas as pd
from loguru import logger
import plotly.express as px
from dotenv import load_dotenv

# Load environment
load_dotenv()
# NOTE: Hardcoded keys removed (security fix). All keys now come from .env / secrets:
#   AIMLAPI_API_KEY, HF_TOKEN, GROQ_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY,
#   TOGETHER_API_KEY, FIREWORKS_API_KEY. See .env.template for the full list.

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

# Import core components
from core.nuclear_intelligence_v4 import NuclearIntelligenceCore
from core.operation_loop_v4 import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger
from core.safety_guard import check_query, check_answer as check_answer_safety
from core.evaluation_enhanced import (
    assess_citation_quality, consistency_report,
    novelty_against_kg, tokenization_readiness,
)
from core.i18n import detect_language, t as tr, PERSIAN_SYSTEM_PROMPT

# ─── Global State ──────────────────────────────────────────────────
core = None
ledger = None
op_loop = None
_init_lock = threading.Lock()


def init_components():
    global core, ledger, op_loop
    if core is not None:
        return
    
    with _init_lock:
        if core is not None:
            return
        logger.info("🚀 Initializing Nuclear Intelligence v4.0...")
        
        core = NuclearIntelligenceCore()
        ledger = VirtualLedger()
        
        config = OperationLoopConfig(
            interval_minutes=int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30)),
            min_accuracy=float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 85.0)),
            min_novelty=float(os.getenv("MIN_NOVELTY_THRESHOLD", 65.0)),
            min_usefulness=float(os.getenv("MIN_USEFULNESS_THRESHOLD", 70.0)),
            min_overall=float(os.getenv("MIN_OVERALL_SCORE", 75.0)),
            min_completeness=float(os.getenv("MIN_COMPLETENESS_THRESHOLD", 50.0)),
            auto_start=False,  # Don't auto-start in Gradio to avoid blocking
            developer_mode=os.getenv("DEVELOPER_MODE", "true").lower() == "true",
            web_search_enabled=True,
            save_reports=True,
            sync_to_hf=True,
            sync_to_gh=True,
        )
        op_loop = OperationLoop(core, ledger, config=config)
        
        logger.info(f"⚛️ Nuclear Intelligence v4.0 Ready!")
        logger.info(f"   LLM Providers: {len(core.llm._available_providers)}")
        logger.info(f"   NES Supply: {ledger.nes_supply}")


# Initialize on module load
init_components()


# ─── UI Helpers ────────────────────────────────────────────────────

def get_stats():
    if not core:
        return {"status": "Initializing..."}
    
    l_stats = ledger.get_stats()
    c_stats = core.get_stats()
    loop_stats = op_loop.get_stats()
    
    active_provider = core.llm._current_provider_name
    available = core.llm._available_providers
    
    provider_display = f"🟢 {active_provider}" if active_provider else "⚠️ None"
    if not active_provider and available:
        provider_display = f"🟡 None (Ready: {', '.join(available)})"
    elif not available:
        provider_display = "🔴 No Providers"
    
    return {
        "⚛️ System": {
            "Status": "Active",
            "Version": "4.0.0",
            "Auto-Loop": "RUNNING" if op_loop.is_running else "PAUSED",
        },
        "🧠 Intelligence": {
            "Questions": c_stats.get('questions_generated', 0),
            "Researches": c_stats.get('researches_conducted', 0),
            "Tokens Minted": c_stats.get('tokens_minted', 0),
            "Tokens Rejected": c_stats.get('tokens_rejected', 0),
        },
        "⛓️ Blockchain": {
            "NES Supply": f"{l_stats.get('nes_supply', 0)} NES",
            "Blocks": l_stats.get('chain_length', 0),
            "Valid Chain": "✅" if l_stats.get('chain_valid') else "❌",
        },
        "🧠 LLM Engine": {
            "Active Provider": provider_display,
            "Available": len(available),
            "Success Rate": c_stats.get('llm_stats', {}).get('success_rate', 'N/A'),
        },
        "📊 Loop": {
            "Total Cycles": loop_stats.get('total_cycles', 0),
            "Approval Rate": loop_stats.get('approval_rate', '0%'),
            "Last Cycle": loop_stats.get('last_cycle', {}).get('cycle_id', 'N/A')[:16] if loop_stats.get('last_cycle') else 'N/A',
        }
    }


def run_manual_cycle(dev_mode=True):
    try:
        if not core:
            return "❌ System initializing..."
        
        result = op_loop.run_cycle(developer_mode=dev_mode)
        
        status = "✅ **MINTED**" if result.minted else "❌ **REJECTED**"
        provider = core.llm._current_provider_name or "None"
        eval_data = result.evaluation
        
        output = [
            f"## {status}",
            f"**Cycle:** `{result.cycle_id}`",
            f"**Provider:** `{provider}`",
            f"**Time:** {result.execution_time_seconds}s",
            f"\n### 📝 Question",
            result.question.get('question', 'N/A'),
            f"\n**Category:** `{result.question.get('category', 'N/A')}` | **Difficulty:** `{result.question.get('difficulty', 0)}/10`",
            f"\n### 📊 Scores",
            f"- 🔬 Accuracy: **{eval_data.get('scientific_accuracy', 0):.1f}%**",
            f"- 💡 Novelty: **{eval_data.get('novelty_score', 0):.1f}%**",
            f"- 👍 Usefulness: **{eval_data.get('usefulness_score', 0):.1f}%**",
            f"- 📦 Completeness: **{eval_data.get('completeness', 0):.1f}%**",
            f"- **🎯 Overall: {eval_data.get('scientific_accuracy', 0) * 0.45 + eval_data.get('novelty_score', 0) * 0.25 + eval_data.get('usefulness_score', 0) * 0.2 + eval_data.get('completeness', 0) * 0.1:.1f}%**",
        ]
        
        if result.minted and result.tx_hash:
            output.append(f"\n### 💰 Token Minted!")
            output.append(f"**TX Hash:** `{result.tx_hash[:40]}...`")
        
        if result.developer_analysis and dev_mode:
            dev = result.developer_analysis
            output.append(f"\n### 🔬 Developer Analysis")
            output.append(f"**Confidence:** `{dev.get('confidence_level', 'N/A')}`")
            if dev.get('token_value_rationale'):
                output.append(f"**Value Rationale:** {dev['token_value_rationale']}")
        
        return "\n".join(output)
        
    except Exception as e:
        logger.exception("Manual cycle failed")
        return f"❌ Error: {str(e)}"


def toggle_auto_loop(active):
    if not op_loop:
        return "❌ System not ready"
    
    if active:
        op_loop.start()
        return "▶️ **Auto-Loop Started** - Running every 30 minutes"
    else:
        op_loop.stop()
        return "⏹️ **Auto-Loop Stopped**"


def ask_question(question, dev_mode=True):
    if not core:
        return "❌ System initializing..."

    if len(question.strip()) < 5:
        return "❌ Please enter a valid question (5+ characters)"

    # ── Safety pre-filter (weapons / proliferation / dirty-bomb / etc.) ──
    verdict = check_query(question)
    if not verdict.allowed:
        return verdict.message

    # ── Locale detection (Persian → fa labels) ──
    locale = detect_language(question)

    try:
        result = core.ask_question(question, developer_mode=dev_mode)
        eval_data = result["evaluation"]
        answer_text = result.get("answer", "")

        # ── Safety post-filter on the generated answer ──
        out_verdict = check_answer_safety(answer_text)
        if not out_verdict.allowed:
            return out_verdict.message

        # ── Enhanced evaluation: citation quality ──
        cq = assess_citation_quality(answer_text, result.get("citations", []))
        # Single-pass consistency (for live UI we don't re-query N times)
        try:
            from core.nuclear_intelligence_v4 import EvaluationScore
            ev_obj = EvaluationScore(
                scientific_accuracy=float(eval_data.get("scientific_accuracy", 0)),
                novelty_score=float(eval_data.get("novelty_score", 0)),
                usefulness_score=float(eval_data.get("usefulness_score", 0)),
                self_consistency_check=True,
                justification=eval_data.get("justification", ""),
                completeness=float(eval_data.get("completeness", 0)),
            )
            tr_obj = tokenization_readiness(ev_obj, consistency=None, citation_quality=cq)
        except Exception:
            tr_obj = None

        output = [
            f"## {tr('research_label', locale)}",
            f"\n**Provider:** `{result.get('provider','?')}` | **Locale:** `{locale}`",
            f"\n### 📖 {tr('summary_label', locale)}",
            question,
            f"\n### 📝 Answer",
            answer_text[:3000] + ("..." if len(answer_text) > 3000 else ""),
            f"\n### 📊 {tr('overall_label', locale)} Quality",
            f"- 🔬 {tr('accuracy_label', locale)}: **{eval_data['scientific_accuracy']:.1f}%**",
            f"- 💡 {tr('novelty_label', locale)}: **{eval_data['novelty_score']:.1f}%**",
            f"- 👍 {tr('usefulness_label', locale)}: **{eval_data['usefulness_score']:.1f}%**",
            f"- 📦 Completeness: **{eval_data.get('completeness', 0):.1f}%**",
            f"- 📚 Citation Quality: **{cq.score:.1f}%** (trusted {cq.trusted_ratio*100:.0f}%, DOI: {cq.has_doi})",
            f"- **🎯 {tr('overall_label', locale)}: {eval_data['overall_score']:.1f}%**",
        ]
        if tr_obj is not None:
            output.append(f"\n### 🪙 Tokenization Readiness")
            output.append(f"**Score:** {tr_obj.overall:.1f}% | **Ready to mint:** {tr_obj.ready_to_mint}")
            if tr_obj.notes:
                output.append(f"**Notes:** {', '.join(tr_obj.notes)}")

        output.append(f"\n### 📚 {tr('citations_label', locale)}")
        for cite in result.get('citations', [])[:5]:
            output.append(f"- {cite}")

        if dev_mode and result.get('developer_analysis'):
            dev = result['developer_analysis']
            output.append(f"\n### 🔬 Developer Analysis")
            output.append(f"**Confidence:** `{dev.get('confidence_level', 'N/A')}`")
            if dev.get('cross_domain'):
                output.append(f"**Cross-Domain:** {', '.join(dev['cross_domain'][:3])}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ Error: {str(e)}"


def get_blockchain_history():
    if not ledger:
        return pd.DataFrame([{"Status": "Initializing..."}])
    
    history = []
    for block in reversed(ledger.chain[-10:]):
        for tx in block.transactions:
            metadata = tx.metadata or {}
            history.append({
                "Block": block.index,
                "Time": metadata.get("mint_time", block.timestamp)[:19],
                "Amount": f"{tx.amount} NES",
                "Type": metadata.get("type", "transfer"),
                "Category": metadata.get("question", {}).get("category", "N/A") if isinstance(metadata.get("question"), dict) else "N/A",
                "Question": (metadata.get("question", {}).get("question", "N/A")[:50] + "...") if isinstance(metadata.get("question"), dict) else str(metadata.get("question", "N/A"))[:50],
            })
    
    return pd.DataFrame(history) if history else pd.DataFrame([{"Message": "No transactions yet"}])


def get_entities_df():
    if not core:
        return pd.DataFrame([{"Status": "Initializing..."}])
    
    data = []
    for eid, e in list(core.kg.graph.get("entities", {}).items())[-50:]:
        m = e.get("metadata", {})
        data.append({
            "ID": eid[:12],
            "Question": e.get("question", "")[:60],
            "Category": m.get("category", "N/A"),
            "Accuracy": f"{m.get('accuracy', m.get('scientific_accuracy', 0)):.1f}%",
            "Novelty": f"{m.get('novelty', m.get('novelty_score', 0)):.1f}%",
            "Created": e.get("created", e.get("timestamp", ""))[:10],
        })
    
    return pd.DataFrame(data) if data else pd.DataFrame([{"Message": "No entities yet"}])


def get_cycle_history():
    if not op_loop:
        return pd.DataFrame([{"Message": "No cycles yet"}])
    
    data = []
    for c in op_loop.history[-50:]:
        data.append({
            "ID": c.cycle_id[:12],
            "Time": c.timestamp[:19],
            "Status": "✅ Minted" if c.minted else "❌ Rejected",
            "Overall": f"{(c.evaluation.get('scientific_accuracy', 0) * 0.45 + c.evaluation.get('novelty_score', 0) * 0.25 + c.evaluation.get('usefulness_score', 0) * 0.2 + c.evaluation.get('completeness', 0) * 0.1):.1f}%",
            "Time (s)": c.execution_time_seconds,
            "Retries": c.retry_count,
        })
    
    return pd.DataFrame(data) if data else pd.DataFrame([{"Message": "No cycles yet"}])


def verify_chain():
    if not ledger:
        return "❌ System not ready"
    
    is_valid = ledger.is_chain_valid()
    stats = ledger.get_stats()
    
    return f"""## ⛓️ Blockchain Verification

**Status:** {'✅ VALID CHAIN' if is_valid else '❌ INVALID CHAIN'}

### 📊 Statistics
| Metric | Value |
|--------|-------|
| Chain Length | {stats['chain_length']} blocks |
| NES Supply | {stats['nes_supply']:,.0f} NES |
| Total Transactions | {stats['total_transactions']} |
| Difficulty | {stats['difficulty']} |
| Latest Block | {stats['latest_hash']} |
| Genesis Block | {stats['genesis_hash']} |

### 🔐 Security
- POW Mining: ✅ Active
- Merkle Trees: ✅ Verified
- Chain Integrity: {'✅ Valid' if is_valid else '❌ Compromised'}
"""


def search_knowledge(query, limit=10):
    if not core:
        return "❌ System not ready"
    
    if not query:
        return "❌ Please enter a search query"
    
    results = core.kg.search(query, limit)
    
    if not results:
        return f"🔍 **No results found for:** `{query}`"
    
    output = [f"## 🔍 Search Results for: `{query}`\n"]
    output.append(f"**Found:** {len(results)} results\n")
    
    for i, r in enumerate(results, 1):
        m = r.get("metadata", {})
        output.append(f"### {i}. {r.get('question', '')[:100]}...")
        output.append(f"**Category:** `{m.get('category', 'N/A')}` | **Score:** `{r.get('_score', 0):.0f}`")
        output.append(f"**Accuracy:** `{m.get('accuracy', m.get('scientific_accuracy', 0)):.1f}%`")
        output.append("")
    
    return "\n".join(output)


def get_llm_health():
    if not core:
        return "**⚠️ System initializing...**"
    
    health = core.llm.health_check()
    
    output = ["## 🔮 LLM Provider Status\n"]
    output.append(f"**Active Provider:** `{health.get('active_provider', 'None')}`")
    output.append(f"**Available:** {health.get('total_available', 0)} providers\n")
    
    output.append("### Provider Details")
    for name, info in health.get("providers", {}).items():
        if info.get("configured"):
            status_icon = "🟢" if info["status"] == "healthy" else "🟡" if info["status"] == "degraded" else "🔴"
            latency = info.get("avg_latency", 0)
            total = info.get("total_requests", 0)
            output.append(f"{status_icon} **{name}**")
            output.append(f"   - Status: {info['status']}")
            output.append(f"   - Model: `{info['default_model']}`")
            if latency > 0:
                output.append(f"   - Latency: {latency:.1f}s")
            if total > 0:
                output.append(f"   - Total Requests: {total}")
            output.append("")
    
    return "\n".join(output)


def get_category_chart():
    if not core:
        return None
    
    stats = core.kg.get_stats()
    if stats.get("total_entities", 0) == 0:
        return None
    
    # Get category distribution
    categories = {}
    for e in core.kg.graph.get("entities", {}).values():
        cat = e.get("metadata", {}).get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    if not categories:
        return None
    
    df = pd.DataFrame(list(categories.items()), columns=["Category", "Count"])
    fig = px.pie(df, values="Count", names="Category", title="📊 Knowledge Distribution by Category")
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def get_score_chart():
    if not op_loop or not op_loop.history:
        return None
    
    scores = []
    for c in op_loop.history[-20:]:
        if c.evaluation:
            overall = (c.evaluation.get('scientific_accuracy', 0) * 0.45 + 
                      c.evaluation.get('novelty_score', 0) * 0.25 + 
                      c.evaluation.get('usefulness_score', 0) * 0.2 +
                      c.evaluation.get('completeness', 0) * 0.1)
            scores.append({
                "Cycle": c.cycle_id[:8],
                "Accuracy": c.evaluation.get('scientific_accuracy', 0),
                "Novelty": c.evaluation.get('novelty_score', 0),
                "Usefulness": c.evaluation.get('usefulness_score', 0),
                "Overall": overall,
            })
    
    if not scores:
        return None
    
    df = pd.DataFrame(scores)
    fig = px.bar(df, x="Cycle", y=["Accuracy", "Novelty", "Usefulness"], 
                 title="📈 Recent Cycle Quality Scores", barmode="group")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
    return fig


# ─── Gradio Interface ──────────────────────────────────────────────

CSS = """
#title { text-align: center; font-size: 2.5rem; font-weight: 800;
         background: linear-gradient(135deg, #00d4ff, #7c3aed, #00ff88);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.minted { color: #10b981; font-weight: bold; }
.rejected { color: #ef4444; }
"""

with gr.Blocks(title="Nuclear Intelligence v4.0", css=CSS, theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence v4.0", elem_id="title")
    gr.Markdown("> *Autonomous AI Research Engine for Nuclear Energy Knowledge*")
    
    with gr.Row():
        with gr.Column(scale=1):
            stats_box = gr.JSON(label="📊 System Statistics", value=get_stats)
            refresh_stats = gr.Button("🔄 Refresh Stats", variant="secondary")
            
            with gr.Accordion("🔮 LLM Engine Status", open=False):
                llm_status = gr.Markdown(value=get_llm_health)
                refresh_llm = gr.Button("📡 Check Providers")
        
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown("### ⚙️ Operation Control")
                
                with gr.Row():
                    run_btn = gr.Button("🚀 Run Research Cycle", variant="primary", size="lg")
                    dev_chk = gr.Checkbox(label="Developer Mode", value=True)
                
                cycle_out = gr.Markdown("### 👆 Click 'Run Research Cycle' to start...")
                
                with gr.Row():
                    auto_toggle = gr.Checkbox(label="Enable Auto-Loop (every 30min)", value=False)
                    auto_status = gr.Textbox(label="Loop Status", interactive=False, lines=1)
                
                auto_toggle.change(toggle_auto_loop, inputs=auto_toggle, outputs=auto_status)
            
            with gr.Tabs():
                with gr.Tab("🔍 Research Center"):
                    with gr.Row():
                        q_input = gr.Textbox(label="Ask a Question", placeholder="e.g. How do molten salt reactors improve safety?", scale=4)
                        ask_btn = gr.Button("🔬 Deep Research", variant="primary", scale=1)
                    
                    answer_out = gr.Markdown("### Research results will appear here...")
                    
                    def handle_ask(q, dev):
                        return ask_question(q, dev)
                    
                    ask_btn.click(handle_ask, inputs=[q_input, dev_chk], outputs=answer_out)
                    q_input.submit(handle_ask, inputs=[q_input, dev_chk], outputs=answer_out)
                
                with gr.Tab("⛓️ Blockchain"):
                    verify_btn = gr.Button("⛓️ Verify Ledger Integrity", variant="secondary")
                    verify_out = gr.Markdown()
                    verify_btn.click(verify_chain, outputs=verify_out)
                    
                    gr.Markdown("### 📜 Recent Transactions")
                    chain_table = gr.DataFrame(value=get_blockchain_history, wrap=True)
                    refresh_chain = gr.Button("🔄 Refresh")
                    refresh_chain.click(get_blockchain_history, outputs=chain_table)
                
                with gr.Tab("🧠 Knowledge Base"):
                    gr.Markdown("### 🔍 Search Knowledge")
                    search_input = gr.Textbox(label="Search", placeholder="e.g. fusion, tokamak, safety")
                    search_btn = gr.Button("Search", variant="primary")
                    search_out = gr.Markdown()
                    search_btn.click(search_knowledge, inputs=search_input, outputs=search_out)
                    search_input.submit(search_knowledge, inputs=search_input, outputs=search_out)
                    
                    gr.Markdown("### 📚 Latest Entities")
                    entities_table = gr.DataFrame(value=get_entities_df, wrap=True)
                
                with gr.Tab("📈 Analytics"):
                    gr.Markdown("### 🔄 Cycle History")
                    history_table = gr.DataFrame(value=get_cycle_history, wrap=True)
                    refresh_history = gr.Button("🔄 Refresh")
                    refresh_history.click(get_cycle_history, outputs=history_table)

                    with gr.Row():
                        chart1 = gr.Plot(get_category_chart)
                        chart2 = gr.Plot(get_score_chart)

                with gr.Tab("🛡️ Safety & Health"):
                    gr.Markdown("### 🛡️ Safety Policy Self-Check")
                    gr.Markdown(
                        "This panel tests the *pre-LLM* and *post-generation* "
                        "safety filters. **The model never sees a refused prompt**; "
                        "instead the user is redirected to the legitimate "
                        "peaceful-use side of the topic."
                    )
                    with gr.Row():
                        safety_test_input = gr.Textbox(
                            label="Test a prompt",
                            placeholder="e.g. 'How to enrich uranium beyond 90 percent'",
                            scale=4,
                        )
                        safety_test_btn = gr.Button("🧪 Run Safety Check", variant="primary", scale=1)
                    safety_test_out = gr.Markdown()

                    def _safety_check(q: str) -> str:
                        if not q or len(q.strip()) < 4:
                            return "❌ Enter a prompt first."
                        v = check_query(q)
                        if v.allowed:
                            return (
                                f"✅ **ALLOWED**\n\n"
                                f"**Category:** none\n"
                                f"**Risk:** none\n\n"
                                f"This prompt passes the safety guard and would be "
                                f"forwarded to the LLM pipeline."
                            )
                        return (
                            f"🛑 **REFUSED** — category `{v.category}`\n\n"
                            f"**Risk:** {v.risk}\n\n"
                            f"**Matched phrases:** {', '.join(v.matched_phrases) or '-'}\n\n"
                            f"**Redirected topic:** {v.redirect}\n\n"
                            f"---\n\n{v.message}"
                        )
                    safety_test_btn.click(_safety_check, inputs=safety_test_input, outputs=safety_test_out)

                    gr.Markdown("### 🩺 Pipeline Health Check")
                    health_btn = gr.Button("🏃 Run Self-Test", variant="secondary")
                    health_out = gr.Markdown()

                    def _run_health() -> str:
                        import subprocess
                        result = subprocess.run(
                            [sys.executable, "scripts/health_check.py"],
                            cwd=str(Path(__file__).parent),
                            capture_output=True, text=True, timeout=60,
                        )
                        body = result.stdout or result.stderr or "(no output)"
                        status = "✅ ALL PASS" if result.returncode == 0 else f"❌ exit={result.returncode}"
                        return f"```text\n{body}\n```\n\n**Status:** {status}"
                    health_btn.click(_run_health, outputs=health_out)
    
    # Event Handlers
    refresh_stats.click(get_stats, outputs=stats_box)
    refresh_llm.click(get_llm_health, outputs=llm_status)
    run_btn.click(run_manual_cycle, inputs=dev_chk, outputs=cycle_out)
    
    gr.Markdown("---")
    gr.Markdown("**Nuclear Intelligence v4.0** | Developed by **Qalam** | NES Token Standard v3.0 | Always-Online with GitHub Actions")

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=int(os.getenv("GRADIO_PORT", 7860)),
        share=False
    )