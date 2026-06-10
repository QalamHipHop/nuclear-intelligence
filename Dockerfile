FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential curl git ffmpeg libgl1-mesa-glx libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p knowledge_base reports exports logs
ENV PYTHONUNBUFFERED=1 GRADIO_SERVER_NAME="0.0.0.0" AUTO_START_LOOP=true DEVELOPER_MODE=false UI_SHARE=true
EXPOSE 7860 8000
CMD ["python3", "-c", "
import uvicorn, threading, sys
sys.path.insert(0, '.')
from api.main import app as fastapi_app
from app import demo
def run_api():
    uvicorn.run(fastapi_app, host='0.0.0.0', port=8000, log_level='info')
thread = threading.Thread(target=run_api, daemon=True)
thread.start()
demo.launch(server_name='0.0.0.0', server_port=7860, share=True)
"]
