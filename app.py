"""
Nuclear Intelligence v3.0 - Advanced Dashboard
═══════════════════════════════════════════════════════════════════
Enhanced Gradio UI with real-time monitoring, developer mode, and beautiful design
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd
from loguru import logger

# Import core components
from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

# ─── Configuration ────────────────────────────────────────────────

accuracy_threshold = float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 93.0))
loop_interval = int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30))
developer_mode = os.getenv("DEVELOPER_MODE", "true").lower() == "true"

logger.info("⚛️ Initializing Nuclear Intelligence v3.0...")

# Initialize core components
core = NuclearIntelligenceCore()
ledger = VirtualLedger()
loop_config = OperationLoopConfig(
    interval_minutes=loop_interval,
    min_accuracy=accuracy_threshold,
    min_novelty=float(os.getenv("MIN_NOVELTY_THRESHOLD", 70.0)),
    min_usefulness=float(os.getenv("MIN_USEFULNESS_THRESHOLD", 75.0)),
    min_overall=float(os.getenv("MIN_OVERALL_SCORE", 82.0)),
    developer_mode=developer_mode,
    auto_start=os.getenv("AUTO_START_LOOP", "true").lower() == "true",
    save_reports=True,
)
op_loop = OperationLoop(core, ledger, config=loop_config)

# Auto-start the operation loop
if os.getenv("AUTO_START_LOOP", "true").lower() == "true":
    threading.Thread(target=op_loop.start, daemon=True).start()
    logger.info("🔄 Operation loop auto-started")


# ─── Helper Functions ────────────────────────────────────────────

def get_llm_status() -> str:
    """Get LLM provider status"""
    stats = core.llm.get_stats()
    health = core.llm.health_check()

    lines = ["**🔮 LLM Engine Status**",
             f"Active Provider: `{stats.get('current_provider', 'unknown')}`",
             f"Available Providers: {len(stats.get('available_providers', []))}",
             f"Total Requests: {stats.get('requests', 0)}",
             f"Success Rate: {stats.get('success_rate', 'N/A')}",
             f"Total Tokens: {stats.get('total_tokens_used', 0):,}",
             f"Cache Hit Rate: {stats.get('cache', {}).get('hit_rate', 'N/A')}"]

    if stats.get('by_provider'):
        lines.append("\n**By Provider:**")
        for p, count in sorted(stats['by_provider'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  • {p}: {count} requests")

    if health.get('providers'):
        lines.append("\n**Provider Health:**")
        for name, info in health['providers'].items():
            status_icon = "🟢" if info['status'] == 'healthy' else "🟡" if info['status'] == 'degraded' else "🔴"
            lines.append(f"  {status_icon} {name}: {info['status']}")

    return "\n".join(lines)


def get_system_stats() -> str:
    """Get comprehensive system statistics"""
    cs = core.get_stats()
    ls = op_loop.get_stats()
    lbs = ledger.get_stats()
    kgs = core.kg.get_stats()

    lines = [
        "## ⚛️ Nuclear Intelligence v3.0",
        f"**Intelligence Engine:**",
        f"  • Questions Generated: {cs.get('questions_generated', 0)}",
        f"  • Researches Conducted: {cs.get('researches_conducted', 0)}",
        f"  • Tokens Minted: {cs.get('tokens_minted', 0)}",
        f"  • Tokens Rejected: {cs.get('tokens_rejected', 0)}",
        f"  • Approval Rate: {cs.get('approval_rate', 'N/A')}",
        f"  • Avg Research Time: {cs.get('avg_research_time', 'N/A')}",
        f"\n**Operation Loop:**",
        f"  • Status: {'🟢 Running' if ls.get('is_running') else '🔴 Stopped'}",
        f"  • Total Cycles: {ls.get('total_cycles', 0)}",
        f"  • Tokens Minted: {ls.get('tokens_minted', 0)}",
        f"  • Avg Cycle Time: {ls.get('average_cycle_time', 'N/A')}",
        f"\n**Blockchain:**",
        f"  • Chain Length: {lbs.get('chain_length', 0)} blocks",
        f"  • NES Supply: {lbs.get('nes_supply', 0)}",
        f"  • Total Transactions: {lbs.get('total_transactions', 0)}",
        f"  • Difficulty: {lbs.get('difficulty', 0)}",
        f"  • Chain Valid: {'✅ Valid' if lbs.get('chain_valid') else '❌ Invalid'}",
        f"\n**Knowledge Graph:**",
        f"  • Entities: {kgs.get('total_entities', 0)}",
        f"  • Relationships: {kgs.get('total_relationships', 0)}",
        f"  • Categories: {len(kgs.get('category_distribution', {}))}",
    ]
    return "\n".join(lines)


def get_blockchain_df() -> pd.DataFrame:
    """Get blockchain data as DataFrame"""
    try:
        data = []
        for block in reversed(ledger.chain):
            for tx in block.transactions:
                meta = tx.metadata or {}
                data.append({
                    "Block": block.index,
                    "Time": block.timestamp[:19],
                    "TX ID": tx.tx_id[:12] + "...",
                    "From": tx.sender[:18] + "..." if len(tx.sender) > 18 else tx.sender,
                    "To": tx.recipient[:18] + "..." if len(tx.recipient) > 18 else tx.recipient,
                    "Amount": tx.amount,
                    "Type": meta.get("type", "transfer"),
                    "Hash": block.hash[:16] + "...",
                })
        return pd.DataFrame(data) if data else pd.DataFrame([{"Message": "No transactions yet"}])
    except Exception as e:
        return pd.DataFrame([{"Error": str(e)}])


def get_entities_df() -> pd.DataFrame:
    """Get knowledge graph entities as DataFrame"""
    try:
        data = []
        for eid, entity in core.kg.graph.get("entities", {}).items():
            meta = entity.get("metadata", {})
            data.append({
                "ID": eid[:12] + "...",
                "Question": entity.get("question", "")[:50] + "...",
                "Category": meta.get("category", "N/A"),
                "Difficulty": meta.get("difficulty", "N/A"),
                "Accuracy": f"{meta.get('accuracy', 0):.1f}%",
                "Novelty": f"{meta.get('novelty', 0):.1f}%",
                "Usefulness": f"{meta.get('usefulness', 0):.1f}%",
                "Provider": meta.get("provider", "N/A"),
                "Created": entity.get("created_at", "")[:10],
            })
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values("Created", ascending=False)
        return df if not df.empty else pd.DataFrame([{"Message": "No entities yet"}])
    except Exception as e:
        return pd.DataFrame([{"Error": str(e)}])


def get_cycle_history_df() -> pd.DataFrame:
    """Get operation cycle history"""
    cycles = op_loop.get_recent_cycles(30)
    if not cycles:
        return pd.DataFrame([{"Message": "No cycles yet"}])

    data = []
    for c in cycles:
        eval_data = c.get("evaluation", {})
        data.append({
            "ID": c.get("cycle_id", "")[:12] + "...",
            "Time": c.get("timestamp", "")[:19],
            "Status": "✅ Minted" if c.get("minted") else "❌ Rejected",
            "Accuracy": f"{eval_data.get('scientific_accuracy', 0):.1f}%",
            "Novelty": f"{eval_data.get('novelty_score', 0):.1f}%",
            "Overall": f"{eval_data.get('scientific_accuracy', 0) * 0.45 + eval_data.get('novelty_score', 0) * 0.25 + eval_data.get('usefulness_score', 0) * 0.20:.1f}%",
            "Time(s)": c.get("execution_time_seconds", 0),
            "TX": (c.get("tx_hash") or "N/A")[:12] + "...",
        })
    return pd.DataFrame(data)


def get_category_chart():
    """Get category distribution pie chart"""
    stats = core.kg.get_category_stats()
    if not stats:
        return None
    import plotly.express as px
    df = pd.DataFrame(list(stats.items()), columns=["Category", "Count"])
    fig = px.pie(
        df, values="Count", names="Category",
        title="Knowledge by Category",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def get_accuracy_novelty_chart():
    """Get accuracy vs novelty scatter chart"""
    entities = list(core.kg.graph.get("entities", {}).values())
    if not entities:
        return None

    data = [
        (e.get("metadata", {}).get("accuracy", 0),
         e.get("metadata", {}).get("novelty", 0),
         e.get("metadata", {}).get("category", "Unknown"))
        for e in entities
    ]
    df = pd.DataFrame(data, columns=["Accuracy", "Novelty", "Category"])

    import plotly.express as px
    fig = px.scatter(
        df, x="Accuracy", y="Novelty", color="Category",
        title="Accuracy vs Novelty by Category",
        labels={"Accuracy": "Scientific Accuracy %", "Novelty": "Novelty Score %"}
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def get_block_time_chart():
    """Get block mining time chart"""
    if len(ledger.chain) < 2:
        return None

    data = []
    for block in ledger.chain[1:]:
        data.append({
            "Block": block.index,
            "Difficulty": block.difficulty,
            "Transactions": block.tx_count,
            "Size (KB)": block.size_bytes / 1024,
        })

    df = pd.DataFrame(data)
    import plotly.express as px
    fig = px.bar(df, x="Block", y="Transactions", title="Transactions per Block")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# ─── Action Functions ─────────────────────────────────────────────

def run_manual_cycle(dev_mode: bool = False) -> str:
    """Run a manual research cycle"""
    try:
        gr.Info("🔄 Running research cycle...")
        result = op_loop.run_cycle(developer_mode=dev_mode)

        status = "✅ **Minted**" if result.minted else "❌ **Rejected**"
        eval_data = result.evaluation
        overall = (
            eval_data.get('scientific_accuracy', 0) * 0.45 +
            eval_data.get('novelty_score', 0) * 0.25 +
            eval_data.get('usefulness_score', 0) * 0.20 +
            eval_data.get('completeness', 0) * 0.10
        )

        output = [
            f"## {status}",
            f"**Cycle ID:** `{result.cycle_id}`",
            f"**Execution Time:** {result.execution_time_seconds}s",
            f"\n### 📝 Question",
            f"{result.question.get('question', 'N/A')}",
            f"\n**Category:** {result.question.get('category')} | **Difficulty:** {result.question.get('difficulty')}/10",
            f"\n### 📊 Evaluation Scores",
            f"- Scientific Accuracy: **{eval_data.get('scientific_accuracy', 0):.1f}%**",
            f"- Novelty Score: **{eval_data.get('novelty_score', 0):.1f}%**",
            f"- Usefulness Score: **{eval_data.get('usefulness_score', 0):.1f}%**",
            f"- Completeness: **{eval_data.get('completeness', 0):.1f}%**",
            f"- **Overall Score: {overall:.1f}%**",
            f"- Self-Consistency: **{'✅ Passed' if eval_data.get('self_consistency_check') else '❌ Failed'}**",
        ]

        if result.tx_hash:
            output.append(f"\n**TX Hash:** `{result.tx_hash[:32]}...`")

        if dev_mode and result.developer_analysis:
            da = result.developer_analysis
            output.append("\n### 🔬 Developer Mode Analysis")
            if da.get("physics_depth"):
                output.append(f"**Physics Depth:**\n{da['physics_depth'][:500]}...")
            if da.get("cross_domain"):
                output.append(f"\n**Cross-Domain Connections:**")
                for cd in da.get("cross_domain", [])[:5]:
                    output.append(f"  • {cd}")
            if da.get("token_value_rationale"):
                output.append(f"\n**Token Value Rationale:** {da['token_value_rationale'][:300]}...")
            if da.get("research_gaps"):
                output.append(f"\n**Research Gaps:**")
                for gap in da.get("research_gaps", [])[:3]:
                    output.append(f"  • {gap}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def ask_question(question: str, dev_mode: bool = False) -> str:
    """Answer a user question"""
    if not question or len(question.strip()) < 5:
        return "❌ Please enter a valid question (at least 5 characters)"

    try:
        gr.Info("🔍 Researching...")
        result = core.ask_question(question, developer_mode=dev_mode)

        eval_data = result.get("evaluation", {})
        output = [
            f"## 🔬 Research Answer",
            f"**Provider:** {result.get('provider', 'Unknown')}",
            f"**Timestamp:** {result.get('timestamp', '')}",
            f"\n### Answer",
            result.get("answer", "No answer generated"),
            f"\n### 📊 Scores",
            f"- Accuracy: **{eval_data.get('scientific_accuracy', 0):.1f}%**",
            f"- Novelty: **{eval_data.get('novelty_score', 0):.1f}%**",
            f"- Usefulness: **{eval_data.get('usefulness_score', 0):.1f}%**",
            f"- **Overall: {eval_data.get('overall_score', 0):.1f}%**",
        ]

        citations = result.get("citations", [])
        if citations:
            output.append("\n### 📚 References")
            for c in citations[:8]:
                output.append(f"  • {c}")

        if dev_mode:
            dev = result.get("developer_analysis", {})
            if dev:
                output.append("\n### 🔬 Developer Analysis")
                if dev.get("cross_domain"):
                    output.append("**Cross-Domain Insights:**")
                    for cd in dev.get("cross_domain", [])[:5]:
                        output.append(f"  • {cd}")
                if dev.get("research_gaps"):
                    output.append("**Research Gaps:**")
                    for gap in dev.get("research_gaps", [])[:3]:
                        output.append(f"  • {gap}")
                if dev.get("confidence_level"):
                    output.append(f"\n**Confidence Level:** {dev['confidence_level']}")

        return "\n".join(output)

    except Exception as e:
        return f"❌ **Error:** {str(e)}"


def toggle_loop(action: str) -> str:
    """Start or stop the operation loop"""
    if action == "start":
        op_loop.start()
        return "✅ Loop started"
    else:
        op_loop.stop()
        return "🛑 Loop stopped"


def export_all() -> str:
    """Export all data"""
    try:
        kg_path = core.kg.export_json()
        chain_path = ledger.export_chain()
        md_path = core.kg.export_markdown()
        return f"✅ Exported:\n• Knowledge Graph: `{kg_path}`\n• Blockchain: `{chain_path}`\n• Markdown: `{md_path}`"
    except Exception as e:
        return f"❌ {str(e)}"


def search_knowledge(query: str, limit: int = 10) -> str:
    """Search knowledge graph"""
    if not query:
        return "❌ Please enter a search query"

    try:
        results = core.kg.search_entities(query, limit=limit)
        if not results:
            return f"🔍 No results found for: **{query}**"

        output = [f"## 🔍 Search Results for: **{query}**\n"]
        for r in results:
            meta = r.get("metadata", {})
            output.append(
                f"\n### {r.get('question', '')[:80]}...\n"
                f"**Category:** {meta.get('category', 'N/A')} | "
                f"**Accuracy:** {meta.get('accuracy', 0):.1f}% | "
                f"**Novelty:** {meta.get('novelty', 0):.1f}%"
            )

        return "\n".join(output)
    except Exception as e:
        return f"❌ Error: {str(e)}"


def verify_chain() -> str:
    """Verify blockchain integrity"""
    is_valid = ledger.is_chain_valid()
    stats = ledger.get_stats()

    output = [
        f"## Blockchain Verification",
        f"**Status:** {'✅ VALID' if is_valid else '❌ INVALID'}",
        f"\n**Statistics:**",
        f"  • Chain Length: {stats.get('chain_length', 0)} blocks",
        f"  • NES Supply: {stats.get('nes_supply', 0)}",
        f"  • Total Transactions: {stats.get('total_transactions', 0)}",
        f"  • Difficulty: {stats.get('difficulty', 0)}",
        f"  • Genesis Hash: `{stats.get('genesis_hash', 'N/A')}`",
        f"  • Latest Hash: `{stats.get('latest_hash', 'N/A')}`",
    ]

    return "\n".join(output)


# ─── CSS Styles ───────────────────────────────────────────────────

CSS = """
#title { text-align: center; font-size: 2.8rem; font-weight: 800; 
         background: linear-gradient(135deg, #00d4ff, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
#subtitle { text-align: center; color: #888; font-size: 1.1rem; }
.status-running { color: #10b981; font-weight: bold; }
.status-stopped { color: #ef4444; font-weight: bold; }
.minted { color: #10b981; }
.rejected { color: #ef4444; }
.gr-button { font-weight: 600; }
"""
THEME = gr.themes.Soft.from_hub("gradio/modern")


# ─── Gradio Interface ─────────────────────────────────────────────

with gr.Blocks(title="⚛️ Nuclear Intelligence v3.0", css=CSS, theme=THEME) as demo:

    # Header
    gr.Markdown(
        "# ⚛️ Nuclear Intelligence Dashboard\n"
        "### AI-Powered Nuclear Energy Research & NES Token System v3.0\n"
        "Powered by DeepSeek, Groq, Gemini, and more free providers",
        elem_id="header"
    )

    # ─── Stats Row ────────────────────────────────────────────────
    with gr.Row():
        nes_stat = gr.Number(label="🪙 NES Supply", value=ledger.nes_supply, interactive=False)
        block_stat = gr.Number(label="⛓️ Blocks", value=len(ledger.chain), interactive=False)
        entity_stat = gr.Number(label="🕸️ Entities", value=len(core.kg.graph.get("entities", {})), interactive=False)
        cycle_stat = gr.Number(label="🔄 Cycles", value=len(op_loop.history), interactive=False)
        provider_stat = gr.Number(label="🤖 LLM Providers", value=len(core.llm._available_providers), interactive=False)

    # ─── Status Row ───────────────────────────────────────────────
    with gr.Row():
        llm_md = gr.Markdown(get_llm_status, label="🔮 LLM Engine")
        sys_md = gr.Markdown(get_system_stats, label="📊 System")

    # ─── Refresh Button ───────────────────────────────────────────
    refresh_btn = gr.Button("🔄 Refresh All Stats", variant="primary", size="lg")
    refresh_btn.click(
        fn=lambda: (
            ledger.nes_supply,
            len(ledger.chain),
            len(core.kg.graph.get("entities", {})),
            len(op_loop.history),
            len(core.llm._available_providers),
            get_llm_status(),
            get_system_stats()
        ),
        outputs=[nes_stat, block_stat, entity_stat, cycle_stat, provider_stat, llm_md, sys_md]
    )

    # ─── Main Tabs ─────────────────────────────────────────────────
    with gr.Tabs():

        # ─── Control Center ──────────────────────────────────────
        with gr.TabItem("🎛️ Control Center"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🚀 Manual Research Cycle")
                    dev_cb = gr.Checkbox(label="🔬 Developer Mode", value=True)
                    run_btn = gr.Button("🚀 Run Research Cycle", variant="primary", size="lg")
                    cycle_out = gr.Markdown("Click 'Run Research Cycle' to start...")
                    gr.Markdown("---")
                    gr.Markdown("### 🔄 Loop Control")
                    loop_status = gr.Markdown(f"**Status:** {'🟢 Running' if op_loop.is_running else '🔴 Stopped'}")
                    with gr.Row():
                        start_btn = gr.Button("▶️ Start Loop", variant="primary")
                        stop_btn = gr.Button("⏹️ Stop Loop", variant="stop")
                    loop_msg = gr.Textbox(label="Status Message", interactive=False)

                with gr.Column(scale=1):
                    gr.Markdown("### 💬 Ask a Question")
                    q_input = gr.Textbox(
                        label="Nuclear Energy Question",
                        placeholder="e.g., What are the latest advances in tokamak plasma confinement?",
                        lines=4
                    )
                    ask_dev_cb = gr.Checkbox(label="🔬 Developer Mode", value=True)
                    ask_btn = gr.Button("🔍 Research Answer", variant="secondary", size="lg")
                    answer_out = gr.Markdown("Enter a question and click 'Research Answer'...")

            run_btn.click(fn=run_manual_cycle, inputs=[dev_cb], outputs=[cycle_out])
            start_btn.click(fn=lambda: toggle_loop("start"), outputs=[loop_msg, loop_status])
            stop_btn.click(fn=lambda: toggle_loop("stop"), outputs=[loop_msg, loop_status])
            ask_btn.click(fn=ask_question, inputs=[q_input, ask_dev_cb], outputs=[answer_out])

        # ─── Blockchain ──────────────────────────────────────────
        with gr.TabItem("⛓️ Blockchain"):
            ref_btn = gr.Button("🔄 Refresh Chain", variant="primary")
            ledger_df = gr.DataFrame(get_blockchain_df, wrap=True, visible=True)
            ref_btn.click(fn=get_blockchain_df, outputs=[ledger_df])

            with gr.Row():
                verify_btn = gr.Button("✅ Verify Chain Integrity", variant="primary")
                verify_out = gr.Textbox(label="Verification Result", interactive=False, lines=5)
            verify_btn.click(fn=verify_chain, outputs=[verify_out])

            with gr.Row():
                block_chart = gr.Plot(get_block_time_chart, label="Block Activity")

        # ─── Knowledge Graph ──────────────────────────────────────
        with gr.TabItem("🕸️ Knowledge Graph"):
            ref_kg_btn = gr.Button("🔄 Refresh", variant="primary")
            entities_df = gr.DataFrame(get_entities_df, wrap=True)

            with gr.Row():
                cat_chart = gr.Plot(get_category_chart, label="Category Distribution")
                acc_chart = gr.Plot(get_accuracy_novelty_chart, label="Accuracy vs Novelty")

            gr.Markdown("### 🔍 Search Knowledge")
            search_input = gr.Textbox(label="Search Query", placeholder="Enter search term...")
            search_limit = gr.Slider(1, 50, value=10, step=1, label="Results Limit")
            search_btn = gr.Button("🔍 Search", variant="secondary")
            search_out = gr.Markdown("")
            export_btn = gr.Button("💾 Export All Data", variant="secondary")
            export_msg = gr.Textbox(label="Export Status", interactive=False)

            ref_kg_btn.click(fn=get_entities_df, outputs=[entities_df])
            search_btn.click(fn=search_knowledge, inputs=[search_input, search_limit], outputs=[search_out])
            export_btn.click(fn=export_all, outputs=[export_msg])

        # ─── Cycle History ────────────────────────────────────────
        with gr.TabItem("📜 Cycle History"):
            hist_df = gr.DataFrame(get_cycle_history_df, wrap=True, label="Recent Cycles")
            gr.Button("🔄 Refresh History").click(fn=get_cycle_history_df, outputs=[hist_df])

        # ─── LLM Provider Management ──────────────────────────────
        with gr.TabItem("🤖 LLM Providers"):
            gr.Markdown("### 🤖 Available LLM Providers")
            gr.Markdown(get_llm_status())

            gr.Markdown("""
            ### 🔑 Free API Key Setup

            Add API keys to `.env` file to enable more providers:

            ```bash
            # DeepSeek V3 - Best free model, 128K context ⭐⭐⭐
            DEEPSEEK_API_KEY=sk-your_key

            # Groq LPU - Fastest inference ⭐⭐⭐
            GROQ_API_KEY=gsk_your_key

            # Google Gemini 2.0 Flash ⭐⭐
            GEMINI_API_KEY=your_key

            # Together AI ⭐⭐
            TOGETHER_API_KEY=tk_your_key

            # OpenRouter (free credits) ⭐
            OPENROUTER_API_KEY=sk-or_your_key

            # Novita AI - DeepSeek V3 ⭐⭐
            NOVITA_API_KEY=your_key

            # Cloudflare Workers AI
            CLOUDFLARE_ACCOUNT_ID=your_account_id
            CLOUDFLARE_API_KEY=your_key

            # HuggingFace (your existing token)
            HF_TOKEN=hf_your_token
            ```

            Restart the application after adding keys.
            """)

        # ─── Settings ────────────────────────────────────────────
        with gr.TabItem("⚙️ Settings"):
            gr.Markdown("""
            ### ⚙️ Configuration Settings

            Current configuration (from `.env`):

            | Setting | Value |
            |---------|-------|
            | Developer Mode | """ + str(developer_mode).upper() + """ |
            | Auto Start Loop | """ + os.getenv("AUTO_START_LOOP", "true").upper() + """ |
            | Loop Interval | """ + str(loop_interval) + """ minutes |
            | Accuracy Threshold | """ + str(accuracy_threshold) + """% |
            | Novelty Threshold | """ + os.getenv("MIN_NOVELTY_THRESHOLD", "70") + """% |
            | Usefulness Threshold | """ + os.getenv("MIN_USEFULNESS_THRESHOLD", "75") + """% |
            | Blockchain Difficulty | """ + str(ledger.difficulty) + """ |

            ### 🔐 Security Features
            - HMAC cryptographic signatures
            - Merkle tree transaction verification
            - POW mining with adaptive difficulty
            - Chain integrity verification
            """)

    # Footer
    gr.Markdown(
        "### ⚛️ Nuclear Intelligence v3.0 | "
        f"Powered by {len(core.llm._available_providers)} LLM providers | "
        f"Total Researches: {core.stats.get('researches_conducted', 0)} | "
        f"NES Supply: {ledger.nes_supply}"
    )


# ─── Main Entry Point ────────────────────────────────────────────

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_PORT", "7860")),
        share=True,
        max_threads=10,
    )