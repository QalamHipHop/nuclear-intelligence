FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p logs reports exports

# Expose ports
EXPOSE 8000 7860

# Start both FastAPI and Gradio
CMD ["sh", "-c", "python api/main.py & python app.py"]
