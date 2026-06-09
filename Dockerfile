FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs knowledge_base/faiss_index

# Initialize knowledge base
RUN python scripts/initialize_knowledge_base.py

# Expose API and Gradio ports
EXPOSE 8000 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with both FastAPI and Gradio
CMD ["sh", "-c", "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 & python app.py"]
