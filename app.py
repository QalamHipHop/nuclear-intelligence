
import gradio as gr
import httpx
import asyncio
import os
from loguru import logger

# Configuration for the FastAPI backend
API_HOST = os.getenv("API_HOST", "http://localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_BASE_URL = f"{API_HOST}:{API_PORT}"

logger.info(f"Gradio app connecting to FastAPI at: {API_BASE_URL}")

async def get_system_status():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/status")
            response.raise_for_status()
            status = response.json()
            return (
                f"**System Status:** {status['status']}\n"
                f"**Timestamp:** {status['timestamp']}\n\n"
                f"**Knowledge Base Summary:**\n"
                f"  Total Answers: {status['knowledge_base']['total_answers']}\n"
                f"  Research History Length: {status['knowledge_base']['research_history_length']}\n"
                f"  Knowledge Graph Nodes: {status['knowledge_base']['knowledge_graph_nodes']}\n"
                f"  Knowledge Graph Edges: {status['knowledge_base']['knowledge_graph_edges']}\n"
                f"  Last Updated: {status['knowledge_base']['last_updated']}\n\n"
                f"**Blockchain State:**\n"
                f"  Chain Length: {status['blockchain']['chain_length']}\n"
                f"  Pending Transactions: {status['blockchain']['pending_transactions']}\n"
                f"  Total NES Minted: {status['blockchain']['total_nes_minted']}\n"
                f"  Last Block Hash: {status['blockchain']['last_block_hash']}\n"
                f"  Blockchain Timestamp: {status['blockchain']['timestamp']}\n\n"
                f"**Operation Loop Stats:**\n"
                f"  Total Cycles: {status['operation_loop']['total_cycles']}\n"
                f"  Successful Cycles: {status['operation_loop']['successful_cycles']}\n"
                f"  Failed Cycles: {status['operation_loop']['failed_cycles']}\n"
                f"  Total Questions Generated: {status['operation_loop']['total_questions_generated']}\n"
                f"  Total Answers Generated: {status['operation_loop']['total_answers_generated']}\n"
                f"  Total Tokens Minted: {status['operation_loop']['total_tokens_minted']}\n"
                f"  Average Accuracy: {status['operation_loop']['average_accuracy']:.2f}%\n"
                f"  Last Cycle Time: {status['operation_loop']['last_cycle_time'] or 'N/A'}"
            )
    except httpx.HTTPStatusError as e:
        return f"Error getting system status: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Network error getting system status: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

async def ask_question_gradio(question: str, category: str, keywords: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/knowledge/ask",
                json={
                    "question": question,
                    "category": category.lower().replace(" ", "_"),
                    "keywords": [k.strip() for k in keywords.split(',') if k.strip()]
                },
                timeout=300.0 # Increased timeout for potentially long LLM calls
            )
            response.raise_for_status()
            answer = response.json()
            sources_text = "\n".join([f"- {s['title']} ({s['url']})" for s in answer['sources']])
            return (
                f"**Question:** {answer['question']}\n\n"
                f"**Answer:**\n{answer['answer']}\n\n"
                f"**Confidence:** {answer['confidence']:.2f}\n"
                f"**Timestamp:** {answer['timestamp']}\n\n"
                f"**Sources:**\n{sources_text}"
            )
    except httpx.HTTPStatusError as e:
        return f"Error asking question: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Network error asking question: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

async def get_knowledge_records_gradio():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/v1/knowledge/records")
            response.raise_for_status()
            records = response.json()
            if not records:
                return "No knowledge records found."
            
            formatted_records = []
            for record in records:
                formatted_records.append(
                    f"**Block Number:** {record['block_number']}\n"
                    f"**Transaction ID:** {record['transaction_id']}\n"
                    f"**Timestamp:** {record['timestamp']}\n"
                    f"**Question:** {record['data']['question']}\n"
                    f"**Answer Hash:** {record['data']['answer_hash']}\n"
                    f"**Evaluation Scores:**\n"
                    f"  Accuracy: {record['data']['evaluation_scores']['scientific_accuracy']:.2f}%\n"
                    f"  Novelty: {record['data']['evaluation_scores']['novelty_score']:.2f}%\n"
                    f"  Usefulness: {record['data']['evaluation_scores']['usefulness_score']:.2f}%\n"
                    f"  Consistency: {record['data']['evaluation_scores']['self_consistency']:.2f}%\n"
                    f"  Overall: {record['data']['evaluation_scores']['overall_score']:.2f}%\n"
                    f"---\n"
                )
            return "\n".join(formatted_records)
    except httpx.HTTPStatusError as e:
        return f"Error getting knowledge records: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Network error getting knowledge records: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

async def trigger_operation_cycle_gradio():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{API_BASE_URL}/api/v1/operations/cycle", timeout=600.0)
            response.raise_for_status()
            result = response.json()
            return (
                f"**Operation Cycle Triggered Successfully!**\n"
                f"Cycle Number: {result['cycle_number']}\n"
                f"Questions Generated: {result['questions_generated']}\n"
                f"Answers Generated: {result['answers_generated']}\n"
                f"Tokens Minted: {result['tokens_minted']}\n"
                f"Timestamp: {result['timestamp']}"
            )
    except httpx.HTTPStatusError as e:
        return f"Error triggering operation cycle: {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Network error triggering operation cycle: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

with gr.Blocks(theme=gr.themes.Soft(), title="Nuclear Intelligence") as demo:
    gr.Markdown("# ⚛️ Nuclear Intelligence Interface")
    gr.Markdown("This interface allows interaction with the Nuclear Intelligence AI system.")

    with gr.Tab("System Status"):
        status_output = gr.Markdown()
        status_button = gr.Button("Refresh System Status")
        status_button.click(get_system_status, outputs=status_output)
        demo.load(get_system_status, outputs=status_output)

    with gr.Tab("Ask Question"):
        with gr.Row():
            question_input = gr.Textbox(label="Your Question", placeholder="e.g., How can SMRs integrate with AI data centers for optimized energy supply?")
            category_input = gr.Dropdown(
                label="Category",
                choices=["Nuclear Physics", "Reactor Engineering", "Safety Management", "Economics", "Applications", "AI Integration"],
                value="AI Integration"
            )
            keywords_input = gr.Textbox(label="Keywords (comma-separated)", placeholder="e.g., SMR, AI, data centers, energy supply")
        ask_button = gr.Button("Ask Nuclear Intelligence")
        answer_output = gr.Markdown()
        ask_button.click(ask_question_gradio, inputs=[question_input, category_input, keywords_input], outputs=answer_output)

    with gr.Tab("Knowledge Records"):
        records_output = gr.Markdown()
        records_button = gr.Button("Refresh Knowledge Records")
        records_button.click(get_knowledge_records_gradio, outputs=records_output)
        demo.load(get_knowledge_records_gradio, outputs=records_output)

    with gr.Tab("Trigger Operation Cycle"):
        cycle_output = gr.Markdown()
        cycle_button = gr.Button("Manually Trigger New Operation Cycle")
        cycle_button.click(trigger_operation_cycle_gradio, outputs=cycle_output)

if __name__ == "__main__":
    # This part is for local development, Hugging Face Spaces will run the app via `app_file` in README.md
    # The FastAPI app needs to be running separately for this to work locally.
    # For HF Spaces, the Dockerfile will handle running both.
    asyncio.run(demo.launch(server_name="0.0.0.0", server_port=7860))
