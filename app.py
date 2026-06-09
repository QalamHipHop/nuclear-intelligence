import gradio as gr
import httpx
import asyncio
import os
from loguru import logger

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

async def get_system_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/status", timeout=10.0)
            status = response.json()
            return f"### System Status: {status['status']}\n\n" \
                   f"**NES Minted:** {status['blockchain']['total_nes_minted']}\n" \
                   f"**Knowledge Nodes:** {status['knowledge_base']['knowledge_graph_nodes']}\n" \
                   f"**Cycles:** {status['operation_loop']['total_cycles']}"
    except Exception as e:
        return f"Error: {e}"

async def trigger_cycle():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/api/v1/operations/cycle", timeout=600.0)
            result = response.json()
            return f"Cycle {result['cycle_number']} completed. Status: {result['status']}"
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks(title="Nuclear Intelligence") as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence (NES)")
    
    with gr.Tab("Dashboard"):
        status_output = gr.Markdown("Loading...")
        refresh_btn = gr.Button("Refresh")
        refresh_btn.click(get_system_status, outputs=status_output)
        
    with gr.Tab("Operations"):
        cycle_btn = gr.Button("Trigger Research Cycle")
        cycle_output = gr.Markdown()
        cycle_btn.click(trigger_cycle, outputs=cycle_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
