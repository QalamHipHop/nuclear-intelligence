
import os
import threading
import time
import gradio as gr
import pandas as pd
from loguru import logger
from datetime import datetime
import json

from core.nuclear_intelligence import NuclearIntelligenceCore
from blockchain.virtual_ledger import VirtualLedger
from core.operation_loop import OperationLoop, OperationLoopConfig

# Initialize System
logger.info("Initializing Nuclear Intelligence System...")

# Load configuration from environment
accuracy_threshold = float(os.getenv("SCIENTIFIC_ACCURACY_THRESHOLD", 93.0))
loop_interval = int(os.getenv("OPERATION_LOOP_INTERVAL_MINUTES", 30))

core = NuclearIntelligenceCore()
ledger = VirtualLedger()
config = OperationLoopConfig(
    min_accuracy=accuracy_threshold,
    interval_minutes=loop_interval
)
op_loop = OperationLoop(core, ledger, config=config)

__all__ = ['demo', 'core', 'ledger', 'op_loop']

def run_manual_cycle():
    try:
        result = op_loop.run_cycle()
        status = "✅ Minted" if result.minted else "❌ Rejected"
        return f"Cycle completed: {status}\nQuestion: {result.question.question}\nAccuracy: {result.evaluation.scientific_accuracy}%"
    except Exception as e:
        return f"Error: {str(e)}"

def get_stats():
    return (
        f"{ledger.nes_supply} NES",
        len(ledger.chain),
        len(core.kg.graph["entities"])
    )

def get_blockchain_df():
    try:
        data = []
        if not ledger or not ledger.chain:
            return pd.DataFrame(columns=["Index", "Timestamp", "Sender", "Recipient", "Amount", "Hash"])
        for block in reversed(ledger.chain):
            for tx in block.transactions:
                data.append({
                    "Index": block.index,
                    "Timestamp": block.timestamp[:19] if block.timestamp else "",
                    "Sender": tx.sender,
                    "Recipient": tx.recipient,
                    "Amount": tx.amount,
                    "Hash": (block.hash[:12] + "...") if block.hash else ""
                })
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Error getting blockchain df: {e}")
        return pd.DataFrame(columns=["Index", "Timestamp", "Sender", "Recipient", "Amount", "Hash"])

def start_background_loop():
    if not op_loop.is_running:
        thread = threading.Thread(target=op_loop.start, daemon=True)
        thread.start()
        return "Background loop started."
    return "Loop already running."

# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence Dashboard")
    gr.Markdown("Autonomous AI Agent for Nuclear Knowledge Tokenization")
    
    with gr.Row():
        nes_stat = gr.Textbox(label="Total NES Supply")
        block_stat = gr.Textbox(label="Blockchain Height")
        kg_stat = gr.Textbox(label="Knowledge Entities")

    with gr.Tabs():
        with gr.TabItem("Control Center"):
            with gr.Row():
                run_btn = gr.Button("🚀 Run Manual Cycle", variant="primary")
                loop_btn = gr.Button("🔄 Start Autonomous Loop")
            output = gr.Textbox(label="Operation Output", lines=10)
            run_btn.click(run_manual_cycle, outputs=output)
            loop_btn.click(start_background_loop, outputs=output)

        with gr.TabItem("Blockchain Ledger"):
            refresh_btn = gr.Button("Refresh Ledger")
            ledger_table = gr.DataFrame(get_blockchain_df())
            refresh_btn.click(get_blockchain_df, outputs=ledger_table)

        with gr.TabItem("Knowledge Graph"):
            kg_display = gr.JSON(core.kg.graph)
            refresh_kg_btn = gr.Button("Refresh Knowledge Graph")
            refresh_kg_btn.click(lambda: core.kg.graph, outputs=kg_display)

    demo.load(get_stats, outputs=[nes_stat, block_stat, kg_stat])

if __name__ == "__main__":
    # Start loop automatically on launch if configured
    if os.getenv("AUTO_START_LOOP", "true").lower() == "true":
        threading.Thread(target=op_loop.start, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False, title="Nuclear Intelligence Dashboard", theme=gr.themes.Soft())
