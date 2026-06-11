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
        auto_start=os.getenv("AUTO_START_LOOP", "true").lower() == "true",
        developer_mode=os.getenv("DEVELOPER_MODE", "true").lower() == "true",
    )
    op_loop = OperationLoop(core, ledger, config=config)
    
    if config.auto_start:
        op_loop.start()
        logger.info("▶️ Autonomous Operation Loop started")

# Initialize on import
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
        "Status": "Running" if op_loop.is_running else "Paused"
    }

def run_manual_cycle():
    result = op_loop.run_cycle(developer_mode=True)
    status = "✅ Minted" if result.minted else "❌ Rejected"
    return f"Cycle {result.cycle_id}: {status}\nAccuracy: {result.evaluation.get('scientific_accuracy', 0):.1f}%\nProvider: {core.llm._current_provider}"

# ─── Gradio Interface ──────────────────────────────────────────────

with gr.Blocks(title="Nuclear Intelligence v1.0.0", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence v1.0.0 Final")
    gr.Markdown("> *Democratizing Nuclear Knowledge for a Digital Civilization*")
    
    with gr.Tab("Dashboard"):
        with gr.Row():
            stats_display = gr.JSON(label="System Statistics", value=get_stats)
            refresh_btn = gr.Button("🔄 Refresh Stats")
            
        with gr.Row():
            cycle_btn = gr.Button("🚀 Run Manual Research Cycle", variant="primary")
            cycle_output = gr.Textbox(label="Last Cycle Result")
            
        refresh_btn.click(get_stats, outputs=stats_display)
        cycle_btn.click(run_manual_cycle, outputs=cycle_output)

    with gr.Tab("Research"):
        query_input = gr.Textbox(label="Ask Nuclear Question", placeholder="e.g. How do molten salt reactors improve safety?")
        ask_btn = gr.Button("🔍 Research")
        answer_output = gr.Markdown(label="Scientific Answer")
        
        def ask(q):
            res = core.ask_question(q, developer_mode=True)
            return f"### Answer\n{res['answer']}\n\n### Evaluation\nAccuracy: {res['evaluation']['scientific_accuracy']}%\nNovelty: {res['evaluation']['novelty_score']}%"
            
        ask_btn.click(ask, inputs=query_input, outputs=answer_output)

    with gr.Tab("Blockchain"):
        gr.Markdown("### Virtual Blockchain Ledger (NES Token)")
        chain_display = gr.JSON(label="Latest Blocks", value=lambda: [b.to_dict() for b in ledger.chain[-5:]])
        
    with gr.Tab("Knowledge Graph"):
        gr.Markdown("### Nuclear Knowledge Entities")
        kg_display = gr.JSON(label="Recent Entities", value=lambda: list(core.kg.graph.get("entities", {}).values())[-5:])

    gr.Markdown("---")
    gr.Markdown("Developed by **Qalam** | Powered by Nuclear Intelligence Core")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_PORT", 7860)))
