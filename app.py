"""
Nuclear Intelligence v1.0.0 Final ⚛️
═══════════════════════════════════════════════════════════════════
Author: Qalam | License: MIT
Ideology: Nuclear Intelligence is a tool for democratizing and rapidly 
expanding nuclear energy knowledge as the foundation for a future of 
abundance, clean, secure, and digital civilization.
═══════════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import gradio as gr
import pandas as pd
from loguru import logger
import plotly.express as px

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

# Import core components
from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

# ─── Global State ──────────────────────────────────────────────────
core = None
ledger = None
op_loop = None

def init_components():
    global core, ledger, op_loop
    if core is not None:
        return
    
    logger.info("🚀 Initializing Nuclear Intelligence v1.0.0...")
    core = NuclearIntelligenceCore()
    ledger = VirtualLedger()
    
    config = OperationLoopConfig(
        interval_minutes=int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30)),
        min_accuracy=float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 93.0)),
        auto_start=os.getenv("AUTO_START_LOOP", "false").lower() == "true",
        developer_mode=os.getenv("DEVELOPER_MODE", "true").lower() == "true",
    )
    op_loop = OperationLoop(core, ledger, config=config)
    
    if config.auto_start:
        op_loop.start()
        logger.info("▶️ Autonomous Operation Loop started")

# Initialize components
init_components()

# ─── UI Helpers ────────────────────────────────────────────────────

def get_stats():
    l_stats = ledger.get_stats()
    c_stats = core.stats
    loop_stats = op_loop.get_stats()
    
    return {
        "NES Supply": f"{l_stats['nes_supply']} NES",
        "Blocks": l_stats['chain_length'],
        "Knowledge Entities": len(core.kg.graph.get("entities", {})),
        "Cycles": loop_stats['total_cycles'],
        "Active Provider": core.llm._current_provider or "None",
        "Auto-Loop": "ACTIVE" if op_loop.is_running else "PAUSED"
    }

def run_manual_cycle():
    result = op_loop.run_cycle(developer_mode=True)
    status = "✅ Minted" if result.minted else "❌ Rejected"
    msg = f"Cycle {result.cycle_id}: {status}\nAccuracy: {result.evaluation.get('scientific_accuracy', 0):.1f}%\nProvider: {core.llm._current_provider}"
    if result.minted:
        msg += f"\nTX Hash: {result.tx_hash}"
    return msg

def toggle_auto_loop(active):
    if active:
        op_loop.start()
        return "▶️ Auto-Loop Started"
    else:
        op_loop.stop()
        return "⏹️ Auto-Loop Stopped"

def get_blockchain_history():
    history = []
    for block in reversed(ledger.chain[-10:]):
        for tx in block.transactions:
            history.append({
                "Block": block.index,
                "Time": tx.metadata.get("mint_time", "N/A"),
                "Amount": f"{tx.amount} NES",
                "Type": tx.metadata.get("type", "transfer"),
                "Question": tx.metadata.get("question", {}).get("question", "N/A")[:50] + "..."
            })
    return pd.DataFrame(history)

# ─── Gradio Interface ──────────────────────────────────────────────

with gr.Blocks(title="Nuclear Intelligence v1.0.0", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence v1.0.0 Final")
    gr.Markdown("> *Democratizing Nuclear Knowledge for a Digital Civilization*")
    
    with gr.Row():
        with gr.Column(scale=1):
            stats_display = gr.JSON(label="System Statistics", value=get_stats)
            refresh_btn = gr.Button("🔄 Refresh Stats")
            
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown("### ⚙️ Operation Control")
                auto_toggle = gr.Checkbox(label="Enable Autonomous Operation Loop", value=op_loop.is_running)
                auto_status = gr.Textbox(label="Loop Status", interactive=False)
                auto_toggle.change(toggle_auto_loop, inputs=auto_toggle, outputs=auto_status)
                
                cycle_btn = gr.Button("🚀 Run Manual Research Cycle", variant="primary")
                cycle_output = gr.Textbox(label="Last Cycle Result", lines=5)
                cycle_btn.click(run_manual_cycle, outputs=cycle_output)

    with gr.Tabs():
        with gr.Tab("Research Center"):
            query_input = gr.Textbox(label="Ask Nuclear Question", placeholder="e.g. How do molten salt reactors improve safety?")
            ask_btn = gr.Button("🔍 Deep Research")
            answer_output = gr.Markdown(label="Scientific Answer")
            
            def ask(q):
                res = core.ask_question(q, developer_mode=True)
                return f"### Answer\n{res['answer']}\n\n### Evaluation\n- **Accuracy**: {res['evaluation']['scientific_accuracy']}%\n- **Novelty**: {res['evaluation']['novelty_score']}%\n- **Usefulness**: {res['evaluation']['usefulness_score']}%"
                
            ask_btn.click(ask, inputs=query_input, outputs=answer_output)

        with gr.Tab("Blockchain Ledger"):
            gr.Markdown("### 🪙 NES Token Minting History")
            history_table = gr.DataFrame(value=get_blockchain_history)
            refresh_history = gr.Button("🔄 Refresh History")
            refresh_history.click(get_blockchain_history, outputs=history_table)
            
            gr.Markdown("### 📦 Latest Blocks")
            chain_display = gr.JSON(label="Block Data", value=lambda: [b.to_dict() for b in ledger.chain[-3:]])

        with gr.Tab("Knowledge Base"):
            gr.Markdown("### 🕸️ Nuclear Knowledge Graph")
            kg_display = gr.JSON(label="Entities", value=lambda: list(core.kg.graph.get("entities", {}).values())[-10:])

    gr.Markdown("---")
    gr.Markdown("Developed by **Qalam** | Version 1.0.0 Final | NES Token Standard v3.0")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_PORT", 7860)))
