"""
Enhanced Gradio UI for Nuclear Intelligence System.
Provides an interactive interface for system monitoring, research execution, and knowledge exploration.
"""

import gradio as gr
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import logging

from core.nuclear_intelligence_enhanced import NuclearIntelligenceCore
from core.enhanced_operation_loop import EnhancedOperationLoop
from blockchain.enhanced_virtual_ledger import EnhancedVirtualLedger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Global State ====================

class UIState:
    """Manages UI state and system components."""
    
    def __init__(self):
        self.config = {
            "llm_model": "gpt-4-turbo",
            "openai_api_key": "your-api-key",
            "blockchain_secret": "nuclear-intelligence-secret",
            "scientific_accuracy_threshold": 93,
            "novelty_threshold": 75,
            "usefulness_threshold": 80,
            "self_consistency_threshold": 90,
            "overall_score_threshold": 85
        }
        self.ni_core = NuclearIntelligenceCore(self.config)
        self.operation_loop = EnhancedOperationLoop(self.config)
        self.ledger = EnhancedVirtualLedger(self.config)
        self.last_cycle_result = None


ui_state = UIState()


# ==================== Helper Functions ====================

def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data for display."""
    return json.dumps(data, indent=2, ensure_ascii=False)


async def execute_research_cycle_async() -> Tuple[str, str, str]:
    """Execute research cycle asynchronously."""
    try:
        result = await ui_state.operation_loop.execute_research_cycle()
        ui_state.last_cycle_result = result
        
        # Format results
        cycle_info = f"""
        **Cycle #{result['cycle_number']}**
        - Start Time: {result['start_time']}
        - Duration: {result['duration_seconds']:.2f} seconds
        - Questions Generated: {result['questions_generated']}
        - Answers Generated: {result['answers_generated']}
        - Tokens Minted: {result['tokens_minted']}
        - Failed Evaluations: {result['failed_evaluations']}
        """
        
        details_json = format_json(result)
        
        # Get chain state
        chain_state = ui_state.ledger.get_chain_state()
        chain_info = f"""
        **Blockchain State**
        - Chain Length: {chain_state['chain_length']}
        - Total NES Minted: {chain_state['total_nes_minted']:.2f}
        - Pending Transactions: {chain_state['pending_transactions']}
        - Last Block Hash: {chain_state['last_block_hash'][:16]}...
        - Chain Integrity: {'✓ Valid' if chain_state['chain_integrity'] else '✗ Invalid'}
        """
        
        return cycle_info, chain_info, details_json
    
    except Exception as e:
        logger.error(f"Error executing research cycle: {e}")
        error_msg = f"Error: {str(e)}"
        return error_msg, "", ""


def execute_research_cycle():
    """Wrapper for executing research cycle in Gradio."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(execute_research_cycle_async())


def get_system_status() -> str:
    """Get current system status."""
    stats = ui_state.operation_loop.get_operation_statistics()
    chain_state = ui_state.ledger.get_chain_state()
    knowledge_summary = ui_state.ni_core.get_knowledge_summary()
    
    status_text = f"""
    # System Status Dashboard
    
    ## Operation Statistics
    - Total Cycles: {stats['total_cycles']}
    - Successful Mints: {stats['successful_mints']}
    - Failed Evaluations: {stats['failed_evaluations']}
    - Success Rate: {stats['success_rate']*100:.1f}%
    
    ## Blockchain State
    - Chain Length: {chain_state['chain_length']}
    - Total NES Minted: {chain_state['total_nes_minted']:.2f}
    - Total Transactions: {chain_state['total_transactions']}
    - Chain Integrity: {'✓ Valid' if chain_state['chain_integrity'] else '✗ Invalid'}
    
    ## Knowledge Base
    - Total Answers: {knowledge_summary['total_answers']}
    - Research History: {knowledge_summary['research_history_length']}
    - Knowledge Graph Nodes: {knowledge_summary['knowledge_graph_nodes']}
    - Knowledge Graph Edges: {knowledge_summary['knowledge_graph_edges']}
    - Vector DB Size: {knowledge_summary['vector_db_size']}
    
    **Last Updated:** {datetime.now().isoformat()}
    """
    
    return status_text


def get_blockchain_records() -> str:
    """Get all knowledge records from blockchain."""
    records = ui_state.ledger.get_knowledge_records()
    
    if not records:
        return "No knowledge records found."
    
    records_text = f"# Knowledge Records ({len(records)} total)\n\n"
    
    for i, record in enumerate(records[-10:], 1):  # Show last 10
        records_text += f"""
        ## Record {i}
        - Block: {record['block']}
        - Transaction: {record['tx'][:16]}...
        - Timestamp: {datetime.fromtimestamp(record['timestamp']).isoformat()}
        - Block Hash: {record['block_hash'][:16]}...
        
        """
    
    return records_text


def get_external_minting_queue() -> str:
    """Get external minting queue."""
    queue = ui_state.ledger.get_external_minting_queue()
    
    if not queue:
        return "External minting queue is empty."
    
    queue_text = f"# External Minting Queue ({len(queue)} pending)\n\n"
    
    for i, item in enumerate(queue, 1):
        queue_text += f"""
        ## Item {i}
        - Transaction ID: {item['tx_id'][:16]}...
        - Status: {item['status']}
        
        """
    
    return queue_text


# ==================== Gradio Interface ====================

def create_interface():
    """Create the Gradio interface."""
    
    with gr.Blocks(title="Nuclear Intelligence System v2.0", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🔬 Nuclear Intelligence System v2.0
        
        Advanced AI-powered autonomous nuclear energy research and knowledge tokenization system.
        
        **Features:**
        - Autonomous question generation and deep research
        - Multi-layer scientific evaluation
        - NES token minting for validated knowledge
        - Blockchain-based knowledge records
        - Real-time system monitoring
        """)
        
        with gr.Tabs():
            # Dashboard Tab
            with gr.Tab("📊 Dashboard"):
                status_output = gr.Markdown()
                refresh_button = gr.Button("🔄 Refresh Status", size="lg")
                refresh_button.click(
                    fn=get_system_status,
                    outputs=status_output
                )
                # Auto-refresh on load
                demo.load(fn=get_system_status, outputs=status_output)
            
            # Research Cycle Tab
            with gr.Tab("🔬 Research Cycle"):
                gr.Markdown("""
                ## Execute Research Cycle
                
                Click the button below to execute a complete research cycle:
                1. Generate complex questions
                2. Conduct deep research
                3. Evaluate answers
                4. Mint NES tokens
                5. Update knowledge base
                """)
                
                execute_button = gr.Button("▶️ Execute Research Cycle", size="lg", variant="primary")
                
                with gr.Row():
                    cycle_info = gr.Textbox(label="Cycle Information", lines=10, interactive=False)
                    chain_info = gr.Textbox(label="Blockchain State", lines=10, interactive=False)
                
                details_output = gr.Textbox(label="Detailed Results (JSON)", lines=15, interactive=False)
                
                execute_button.click(
                    fn=execute_research_cycle,
                    outputs=[cycle_info, chain_info, details_output]
                )
            
            # Blockchain Tab
            with gr.Tab("⛓️ Blockchain"):
                with gr.Row():
                    records_output = gr.Markdown()
                    queue_output = gr.Markdown()
                
                refresh_blockchain_button = gr.Button("🔄 Refresh Blockchain Data")
                
                def refresh_blockchain():
                    return get_blockchain_records(), get_external_minting_queue()
                
                refresh_blockchain_button.click(
                    fn=refresh_blockchain,
                    outputs=[records_output, queue_output]
                )
                
                # Auto-refresh on load
                demo.load(fn=refresh_blockchain, outputs=[records_output, queue_output])
            
            # Configuration Tab
            with gr.Tab("⚙️ Configuration"):
                gr.Markdown("""
                ## System Configuration
                
                Current evaluation thresholds:
                """)
                
                with gr.Row():
                    gr.Textbox(
                        value=str(ui_state.config["scientific_accuracy_threshold"]),
                        label="Scientific Accuracy Threshold",
                        interactive=False
                    )
                    gr.Textbox(
                        value=str(ui_state.config["novelty_threshold"]),
                        label="Novelty Threshold",
                        interactive=False
                    )
                
                with gr.Row():
                    gr.Textbox(
                        value=str(ui_state.config["usefulness_threshold"]),
                        label="Usefulness Threshold",
                        interactive=False
                    )
                    gr.Textbox(
                        value=str(ui_state.config["self_consistency_threshold"]),
                        label="Self-Consistency Threshold",
                        interactive=False
                    )
                
                gr.Textbox(
                    value=str(ui_state.config["overall_score_threshold"]),
                    label="Overall Score Threshold",
                    interactive=False
                )
                
                gr.Markdown("""
                **Note:** Configuration values are set at system startup.
                To modify thresholds, update the configuration file and restart the system.
                """)
            
            # About Tab
            with gr.Tab("ℹ️ About"):
                gr.Markdown("""
                ## About Nuclear Intelligence System v2.0
                
                **Version:** 2.0.0  
                **Status:** Production Ready  
                **Last Updated:** 2026-06-09
                
                ### System Components
                
                1. **Nuclear Intelligence Core (NI Core)**
                   - Advanced RAG with vector database and reranking
                   - Knowledge Graph integration
                   - Multi-layer evaluation system
                
                2. **Enhanced Virtual Ledger**
                   - Full blockchain features with Merkle trees
                   - NES token minting and management
                   - External network synchronization
                
                3. **Operation Loop**
                   - Autonomous research cycle orchestration
                   - Continuous operation with error recovery
                   - Comprehensive logging and monitoring
                
                4. **FastAPI Backend**
                   - RESTful API for system integration
                   - Real-time monitoring endpoints
                   - External blockchain integration
                
                ### Key Features
                
                - **Autonomous Operation:** Runs continuously without human intervention
                - **Scientific Rigor:** Multi-layer evaluation ensures high-quality knowledge
                - **Tokenization:** Validated knowledge is automatically tokenized as NES
                - **Transparency:** All operations recorded on immutable blockchain
                - **Scalability:** Designed for continuous expansion of knowledge base
                
                ### Project Links
                
                - **GitHub:** https://github.com/QalamHipHop/nuclear-intelligence
                - **Hugging Face:** https://huggingface.co/spaces/Qalam/Nuclear-Intelligence
                
                ---
                
                **Developed by:** Qalam Hip Hop  
                **Powered by:** Advanced AI & Blockchain Technology
                """)
    
    return demo


# ==================== Main Execution ====================

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
