import gradio as gr
import httpx
import asyncio
import os
import json
from loguru import logger

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

async def get_system_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/status", timeout=10.0)
            status = response.json()
            
            md = f"### ⚛️ System Status: {status['status'].upper()}\n\n"
            md += "| Metric | Value |\n| :--- | :--- |\n"
            md += f"| **Total NES Minted** | {status['blockchain']['total_nes_minted']} |\n"
            md += f"| **Knowledge Nodes** | {status['knowledge_base']['knowledge_graph_nodes']} |\n"
            md += f"| **Successful Cycles** | {status['operation_loop']['successful_cycles']} |\n"
            md += f"| **Average Accuracy** | {status['operation_loop']['average_accuracy']:.2f}% |\n"
            md += f"| **Last Updated** | {status['timestamp']} |\n"
            return md
    except Exception as e:
        return f"### ⚠️ Error Connecting to API\n\n{str(e)}"

async def trigger_cycle():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/api/v1/operations/cycle", timeout=600.0)
            result = response.json()
            
            md = f"### ✅ Cycle {result['cycle_number']} Completed\n\n"
            md += f"**Status:** {result['status']}\n\n"
            
            if result.get('tokens_minted'):
                md += "#### 🪙 NES Tokens Minted:\n"
                for mint in result['tokens_minted']:
                    token = mint['token_data']
                    md += f"- **ID:** `{mint['tx_id'][:12]}` | **Accuracy:** {token['evaluation_scores']['scientific_accuracy']}% | **Novelty:** {token['evaluation_scores']['novelty_score']}%\n"
            
            return md
    except Exception as e:
        return f"### ❌ Error Triggering Cycle\n\n{str(e)}"

async def get_blockchain_ledger():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/blockchain/ledger", timeout=10.0)
            ledger = response.json()
            return json.dumps(ledger, indent=2)
    except Exception as e:
        return f"Error: {e}"

with gr.Blocks(title="Nuclear Intelligence", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence (NES)")
    gr.Markdown("Autonomously expanding and tokenizing nuclear energy knowledge.")
    
    with gr.Tabs():
        with gr.Tab("Dashboard"):
            with gr.Row():
                with gr.Column():
                    status_output = gr.Markdown("Click Refresh to load status...")
                    refresh_btn = gr.Button("🔄 Refresh Status", variant="primary")
                    refresh_btn.click(get_system_status, outputs=status_output)
                
                with gr.Column():
                    gr.Markdown("### 🚀 Operations")
                    cycle_btn = gr.Button("⚡ Trigger Research Cycle", variant="secondary")
                    cycle_output = gr.Markdown()
                    cycle_btn.click(trigger_cycle, outputs=cycle_output)
        
        with gr.Tab("Blockchain Ledger"):
            ledger_btn = gr.Button("View Full Ledger")
            ledger_output = gr.Code(language="json")
            ledger_btn.click(get_blockchain_ledger, outputs=ledger_output)
            
        with gr.Tab("About NES"):
            gr.Markdown("""
            ## NES: Nuclear Energy Stablecoin
            
            NES is backed by validated scientific knowledge. Every token represents a unique advancement in nuclear science:
            - **Scientific Accuracy:** Each claim is verified by high-level AI research.
            - **Novelty:** Rewards original insights and multidimensional analysis.
            - **Immutability:** Records are stored on a virtual blockchain for full auditability.
            """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
