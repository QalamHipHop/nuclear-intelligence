
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
core = NuclearIntelligenceCore()
ledger = VirtualLedger()
op_loop = OperationLoop(core, ledger)

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
    data = []
    for block in reversed(ledger.chain):
        for tx in block.transactions:
            data.append({
                "Index": block.index,
                "Timestamp": block.timestamp[:19],
                "Sender": tx.sender,
                "Recipient": tx.recipient,
                "Amount": tx.amount,
                "Hash": block.hash[:12] + "..."
            })
    return pd.DataFrame(data)

def start_background_loop():
    if not op_loop.is_running:
        thread = threading.Thread(target=op_loop.start, daemon=True)
        thread.start()
        return "Background loop started."
    return "Loop already running."

# Gradio Interface
with gr.Blocks(title="Nuclear Intelligence Dashboard", theme=gr.themes.Soft()) as demo:
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
            gr.JSON(core.kg.graph)

    demo.load(get_stats, outputs=[nes_stat, block_stat, kg_stat])

if __name__ == "__main__":
    # Start loop automatically on launch
    threading.Thread(target=op_loop.start, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860)
