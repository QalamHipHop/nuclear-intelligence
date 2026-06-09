
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import demo, core, ledger, op_loop
from api.enhanced_api import app, init_components
import threading
import uvicorn

# Initialize API components
init_components(core, ledger, op_loop)

# This file serves as the entry point for Hugging Face Spaces.
# It launches the Gradio demo on port 7860 and the FastAPI app on port 8000.

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Start FastAPI in a background thread
    threading.Thread(target=run_fastapi, daemon=True).start()
    
    # Start Gradio in the main thread
    demo.launch(server_name="0.0.0.0", server_port=7860)
