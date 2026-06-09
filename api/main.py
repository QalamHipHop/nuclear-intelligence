
import sys
import os

# Add the parent directory to the Python path to allow imports from `core` and `blockchain`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import demo

# This file serves as the entry point for Hugging Face Spaces.
# It imports the Gradio demo from app.py and launches it.

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
