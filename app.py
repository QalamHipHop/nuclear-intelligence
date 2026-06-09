
import gradio as gr
import os
import threading
import logging
import json

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from core.operation_loop import OperationLoop, OperationLoopConfig
from blockchain.virtual_ledger import VirtualLedger

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize core components
ni_core = NuclearIntelligenceCore()
virtual_ledger = VirtualLedger()

# Configure and initialize the operation loop
op_config = OperationLoopConfig(
    question_generation_context="Focus on breakthroughs in nuclear fusion, advanced reactor safety, and economic models for sustainable nuclear energy.",
    min_scientific_accuracy=93.0,
    loop_interval_seconds=1800 # 30 minutes
)
operation_loop = OperationLoop(ni_core, virtual_ledger, op_config)

# Function to run the operation loop in a separate thread
def start_operation_loop():
    logging.info("Starting the Nuclear Intelligence operation loop in background...")
    operation_loop.start_loop()

# Start the operation loop in a daemon thread so it doesn't block the main app
loop_thread = threading.Thread(target=start_operation_loop, daemon=True)
loop_thread.start()

# Gradio Interface Functions
def get_current_status():
    latest_block = virtual_ledger.get_last_block()
    status_text = f"**Nuclear Intelligence System Status**\n\n"
    status_text += f"**Total NES Supply:** {virtual_ledger.nes_supply:.2f}\n"
    status_text += f"**Blockchain Valid:** {virtual_ledger.is_chain_valid()}\n"
    status_text += f"**Last Block Index:** {latest_block.index}\n"
    status_text += f"**Last Block Hash:** {latest_block.hash[:20]}...\n"
    status_text += f"**Pending Transactions:** {len(virtual_ledger.pending_transactions)}\n\n"
    status_text += f"**Knowledge Graph Entities:** {sum(len(v) for v in ni_core.knowledge_graph.graph.values())}\n"
    status_text += f"**LLM Model:** {ni_core.llm.model_name}\n"
    status_text += f"**Embedding Model:** {ni_core.embeddings.model_name}\n"
    return status_text

def run_manual_cycle():
    logging.info("Manually triggering a single operation cycle...")
    operation_loop.run_single_cycle()
    return get_current_status()

def get_blockchain_data():
    return json.dumps([block.to_dict() for block in virtual_ledger.chain], indent=2)

def get_knowledge_graph_data():
    return json.dumps(ni_core.knowledge_graph.graph, indent=2)

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("# Nuclear Intelligence Agent & Stablecoin")
    gr.Markdown("This space hosts the Nuclear Intelligence AI Agent, which autonomously researches nuclear energy, mints NES stablecoins based on validated knowledge, and maintains a virtual blockchain.")

    with gr.Tab("System Status"):
        status_output = gr.Textbox(label="Current System Status", lines=10, interactive=False)
        refresh_status_btn = gr.Button("Refresh Status")
        refresh_status_btn.click(get_current_status, outputs=status_output)
        demo.load(get_current_status, outputs=status_output, every=30) # Auto-refresh every 30 seconds

    with gr.Tab("Manual Operation"):
        gr.Markdown("Trigger a single research and minting cycle manually.")
        manual_cycle_btn = gr.Button("Run Single Operation Cycle")
        manual_cycle_output = gr.Textbox(label="Manual Cycle Result", lines=10, interactive=False)
        manual_cycle_btn.click(run_manual_cycle, outputs=manual_cycle_output)

    with gr.Tab("Blockchain Explorer"):
        blockchain_output = gr.JSON(label="Virtual Blockchain Data")
        refresh_blockchain_btn = gr.Button("Refresh Blockchain Data")
        refresh_blockchain_btn.click(get_blockchain_data, outputs=blockchain_output)

    with gr.Tab("Knowledge Graph Explorer"):
        knowledge_graph_output = gr.JSON(label="Knowledge Graph Data")
        refresh_kg_btn = gr.Button("Refresh Knowledge Graph Data")
        refresh_kg_btn.click(get_knowledge_graph_data, outputs=knowledge_graph_output)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

