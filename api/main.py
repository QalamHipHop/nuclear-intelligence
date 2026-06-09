
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import demo

# This file serves as the entry point for Hugging Face Spaces.
# It imports the Gradio demo from app.py and launches it on port 7860.

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
