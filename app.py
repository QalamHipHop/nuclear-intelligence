"""
Nuclear Intelligence - Main Application (Gradio UI) v2.0
Advanced dashboard with developer mode and free LLM providers
"""
import os, sys, json, threading, time
from datetime import datetime
from pathlib import Path
import gradio as gr
import pandas as pd
from loguru import logger

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

accuracy_threshold = float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 93.0))
loop_interval = int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30))
developer_mode = os.getenv("DEVELOPER_MODE", "false").lower() == "true"

logger.info("Initializing Nuclear Intelligence v2.0...")

core = NuclearIntelligenceCore()
ledger = VirtualLedger()
loop_config = OperationLoopConfig(interval_minutes=loop_interval, min_accuracy=accuracy_threshold, developer_mode=developer_mode)
op_loop = OperationLoop(core, ledger, config=loop_config)

if os.getenv("AUTO_START_LOOP", "true").lower() == "true":
    threading.Thread(target=op_loop.start, daemon=True).start()
    logger.info("Operation loop auto-started")

def get_llm_status():
    stats = core.llm.get_stats()
    lines = [f"**🔮 LLM Engine Status**", f"Active Provider: `{stats.get('current_provider','unknown')}`",
             f"Providers: {', '.join(stats.get('available_providers',[])) or 'None configured'}",
             f"Requests: {stats.get('requests',0)} | Success: {stats.get('success_rate','N/A')}"]
    if stats.get('by_provider'):
        lines.append(f"\n**By Provider:**")
        for p, c in stats['by_provider'].items(): lines.append(f"  - {p}: {c}")
    return "\n".join(lines)

def get_system_stats():
    cs, ls, lbs, kgs = core.get_stats(), op_loop.get_stats(), ledger.get_stats(), core.kg.get_stats()
    lines = [f"**⚛️ Nuclear Intelligence v2.0**",
             f"\n🧠 Intelligence: {cs.get('questions_generated',0)} Q | {cs.get('researches_conducted',0)} R | {cs.get('tokens_minted',0)} minted | {cs.get('approval_rate','N/A')}",
             f"\n🔄 Loop: {'🟢 Running' if ls.get('is_running') else '🔴 Stopped'} | {ls.get('total_cycles',0)} cycles | Avg {ls.get('average_cycle_time','N/A')}",
             f"\n⛓️ Blockchain: {lbs.get('chain_length',0)} blocks | {lbs.get('nes_supply',0)} NES | {lbs.get('total_transactions',0)} TX | {'✅ Valid' if lbs.get('chain_valid') else '❌ Invalid'}",
             f"\n🕸️ Knowledge Graph: {kgs.get('total_entities',0)} entities | {len(kgs.get('category_distribution',{}))} categories"]
    return "\n".join(lines)

def get_blockchain_df():
    try:
        data = []
        for block in reversed(ledger.chain):
            for tx in block.transactions:
                data.append({"Block": block.index, "Timestamp": block.timestamp[:19], "TX ID": tx.tx_id[:12]+"...",
                             "From": tx.sender[:20]+"..." if len(tx.sender)>20 else tx.sender,
                             "To": tx.recipient[:20]+"..." if len(tx.recipient)>20 else tx.recipient,
                             "Amount": tx.amount, "Hash": block.hash[:16]+"..."})
        return pd.DataFrame(data)
    except: return pd.DataFrame([{"Error": "No data"}])

def get_entities_df():
    try:
        data = []
        for eid, entity in core.kg.graph["entities"].items():
            meta = entity.get("metadata", {})
            data.append({"ID": eid[:12]+"...", "Question": entity.get("question","")[:60]+"...",
                         "Category": meta.get("category","N/A"), "Diff": meta.get("difficulty","N/A"),
                         "Accuracy": f"{meta.get('accuracy',0):.1f}%", "Novelty": f"{meta.get('novelty',0):.1f}%",
                         "Created": entity.get("created_at","")[:10]})
        return pd.DataFrame(sorted(data, key=lambda x: x["Created"], reverse=True))
    except: return pd.DataFrame([{"Error": "No data"}])

def get_category_chart():
    stats = core.kg.get_category_stats()
    if not stats: return None
    import plotly.express as px
    df = pd.DataFrame(list(stats.items()), columns=["Category","Count"])
    fig = px.pie(df, values="Count", names="Category", title="Knowledge by Category", color_discrete_sequence=px.colors.qualitative.Bold)
    fig.update_layout(height=400)
    return fig

def get_accuracy_chart():
    entities = list(core.kg.graph["entities"].values())
    if not entities: return None
    data = [(e.get("metadata",{}).get("accuracy",0), e.get("metadata",{}).get("novelty",0)) for e in entities]
    df = pd.DataFrame(data, columns=["Accuracy","Novelty"])
    import plotly.express as px
    fig = px.scatter(df, x="Accuracy", y="Novelty", title="Accuracy vs Novelty", labels={"Accuracy":"Scientific Accuracy %","Novelty":"Novelty Score %"})
    fig.update_layout(height=400)
    return fig

def run_manual_cycle(dev_mode=False):
    try:
        result = op_loop.run_cycle(developer_mode=dev_mode)
        status = "✅ **Minted**" if result.minted else "❌ **Rejected**"
        output = [f"## {status} | Cycle: `{result.cycle_id}` | Time: {result.execution_time_seconds}s",
                 f"### Question\n{result.question.get('question','N/A')}",
                 f"**Category:** {result.question.get('category')} | **Difficulty:** {result.question.get('difficulty')}/10",
                 f"\n### Scores\n- Accuracy: **{result.evaluation.get('scientific_accuracy',0):.1f}%**",
                 f"- Novelty: **{result.evaluation.get('novelty_score',0):.1f}%**",
                 f"- Usefulness: **{result.evaluation.get('usefulness_score',0):.1f}%**",
                 f"- Consistent: **{'✅' if result.evaluation.get('self_consistency_check') else '❌'}**"]
        if result.tx_hash: output.append(f"\n**TX Hash:** `{result.tx_hash[:32]}...`")
        if dev_mode and result.developer_analysis:
            da = result.developer_analysis
            output.append("\n### 🔬 Developer Mode")
            if da.get("physics_depth"): output.append(f"**Physics:** {da['physics_depth'][:200]}...")
            if da.get("token_value_rationale"): output.append(f"**Token Value:** {da['token_value_rationale'][:200]}...")
        return "\n".join(output)
    except Exception as e:
        return f"❌ **Error:** {str(e)}"

def ask_question(question, dev_mode=False):
    try:
        q = ResearchQuestion(question=question, category="User Query", difficulty=5, keywords=[])
        answer = core.conduct_research(q, use_web_search=True)
        if not answer: return "❌ Research failed"
        evaluation = core.evaluate_answer(q, answer)
        output = [f"## Research Answer\n**Model:** {core.llm._current_provider or 'Unknown'}\n\n{answer.answer}",
                  f"\n### Scores\nAccuracy: **{evaluation.scientific_accuracy:.1f}%** | Novelty: **{evaluation.novelty_score:.1f}%** | Usefulness: **{evaluation.usefulness_score:.1f}%**"]
        if answer.citations:
            output.append("\n### References")
            for c in answer.citations[:5]: output.append(f"- {c}")
        if dev_mode:
            dev = core.developer_mode_analysis(q, answer)
            if dev.get("cross_domain"):
                output.append("\n### 🔬 Cross-Domain Insights")
                for cd in dev.get("cross_domain",[])[:3]: output.append(f"  - {cd}")
        return "\n".join(output)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def toggle_loop(action):
    if action == "start": op_loop.start()
    else: op_loop.stop()
    return f"{'✅ Loop started' if action=='start' else '🛑 Loop stopped'}"

def export_all():
    try:
        kg_path = core.kg.export_json()
        chain_path = ledger.export_chain()
        md_path = core.kg.export_markdown()
        return f"✅ Exported:\n- KG JSON: `{kg_path}`\n- Blockchain: `{chain_path}`\n- KG Markdown: `{md_path}`"
    except Exception as e: return f"❌ {str(e)}"

def get_cycle_history_df():
    cycles = op_loop.get_recent_cycles(20)
    if not cycles: return pd.DataFrame([{"Message":"No cycles yet"}])
    return pd.DataFrame([{"ID": c.get("cycle_id","")[:12]+"...", "Time": c.get("timestamp","")[:19],
                          "Status": "✅ Minted" if c.get("minted") else "❌ Rejected",
                          "Accuracy": f"{c.get('evaluation',{}).get('scientific_accuracy',0):.1f}%",
                          "Time(s)": c.get("execution_time_seconds",0),
                          "TX": (c.get("tx_hash") or "N/A")[:12]+"..."} for c in cycles])

css = "#title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #00d4ff; } #subtitle { text-align: center; color: #888; }"

with gr.Blocks(title="Nuclear Intelligence ⚛️", css=css) as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence Dashboard\n### AI-Powered Nuclear Energy Research & NES Token System v2.0", elem_id="header")

    with gr.Row():
        nes_stat = gr.Number(label="🪙 NES Supply", value=ledger.nes_supply, interactive=False)
        block_stat = gr.Number(label="⛓️ Blocks", value=len(ledger.chain), interactive=False)
        entity_stat = gr.Number(label="🕸️ Entities", value=len(core.kg.graph["entities"]), interactive=False)
        cycle_stat = gr.Number(label="🔄 Cycles", value=len(op_loop.history), interactive=False)

    with gr.Row():
        llm_md = gr.Markdown(get_llm_status, label="🔮 LLM Engine")
        sys_md = gr.Markdown(get_system_stats, label="📊 System")

    refresh_btn = gr.Button("🔄 Refresh All", variant="primary")
    refresh_btn.click(lambda: (ledger.nes_supply, len(ledger.chain), len(core.kg.graph["entities"]), len(op_loop.history), get_llm_status(), get_system_stats()),
                      outputs=[nes_stat, block_stat, entity_stat, cycle_stat, llm_md, sys_md])

    with gr.Tabs():
        with gr.TabItem("🎛️ Control Center"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🚀 Manual Cycle")
                    dev_cb = gr.Checkbox(label="🔬 Developer Mode", value=False)
                    run_btn = gr.Button("🚀 Run Research Cycle", variant="primary", size="lg")
                    cycle_out = gr.Markdown("Run a cycle...")
                with gr.Column():
                    gr.Markdown("### 🔄 Loop Control")
                    loop_md = gr.Markdown(f"**Status:** {'🟢 Running' if op_loop.is_running else '🔴 Stopped'}")
                    with gr.Row():
                        start_btn = gr.Button("▶️ Start", variant="primary")
                        stop_btn = gr.Button("⏹️ Stop", variant="stop")
                    loop_msg = gr.Textbox(interactive=False)
            with gr.Row():
                gr.Markdown("### 💬 Ask a Question")
                q_input = gr.Textbox(label="Nuclear Question", placeholder="e.g., What are the latest advances in tokamak plasma confinement?", lines=3)
                ask_dev_cb = gr.Checkbox(label="🔬 Developer Mode", value=False)
                ask_btn = gr.Button("🔍 Research Answer", variant="secondary")
                answer_out = gr.Markdown("")
            run_btn.click(run_manual_cycle, inputs=[dev_cb], outputs=[cycle_out])
            start_btn.click(lambda: toggle_loop("start"), outputs=[loop_msg])
            stop_btn.click(lambda: toggle_loop("stop"), outputs=[loop_msg])
            ask_btn.click(ask_question, inputs=[q_input, ask_dev_cb], outputs=[answer_out])

        with gr.TabItem("⛓️ Blockchain"):
            ref_btn = gr.Button("🔄 Refresh")
            ledger_df = gr.DataFrame(get_blockchain_df, wrap=True)
            ref_btn.click(get_blockchain_df, outputs=[ledger_df])
            with gr.Row():
                verify_btn = gr.Button("✅ Verify Chain")
                verify_out = gr.Textbox(interactive=False)
            verify_btn.click(lambda: "✅ Valid" if ledger.is_chain_valid() else "❌ Invalid", outputs=[verify_out])

        with gr.TabItem("🕸️ Knowledge Graph"):
            ref_kg_btn = gr.Button("🔄 Refresh")
            export_btn = gr.Button("💾 Export All")
            export_msg = gr.Textbox(interactive=False)
            ref_kg_btn.click(get_entities_df, outputs=[entities_df := gr.DataFrame()])
            export_btn.click(export_all, outputs=[export_msg])
            with gr.Row():
                cat_chart = gr.Plot(get_category_chart)
                acc_chart = gr.Plot(get_accuracy_chart)

        with gr.TabItem("📜 Cycle History"):
            hist_df = gr.DataFrame(get_cycle_history_df, wrap=True)
            gr.Button("🔄 Refresh").click(get_cycle_history_df, outputs=[hist_df])

        with gr.TabItem("⚙️ Settings"):
            gr.Markdown("""### 🔑 Free LLM Provider Setup

Add at least ONE of these API keys to `.env`:

```bash
# Groq (Recommended - Fastest free LPU)
GROQ_API_KEY=gsk_your_key   # https://console.groq.com

# Together AI
TOGETHER_API_KEY=tk_your_key  # https://api.together.xyz

# OpenRouter (free credits)
OPENROUTER_API_KEY=sk-or_your_key  # https://openrouter.ai

# HuggingFace (you already have the token!)
HF_TOKEN=hf_your_token  # https://huggingface.co/settings/tokens
```

**Current Providers:** """ + ', '.join(core.llm._available_providers) or 'None configured')
            gr.Markdown(f"**Active Provider:** {core.llm._current_provider or 'None'}\n**Developer Mode:** {'✅ On' if developer_mode else '❌ Off'}\n**Loop Running:** {'🟢 Yes' if op_loop.is_running else '🔴 No'}")

__all__ = ['demo', 'core', 'ledger', 'op_loop']
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
