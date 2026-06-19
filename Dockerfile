# Nuclear Intelligence v1.0.0 Final - Dockerfile
FROM python:3.11-slim

# Install system dependencies for FAISS and other libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create necessary directories
RUN mkdir -p knowledge_base reports logs

# Environment variables
ENV GRADIO_PORT=7860
ENV HF_SPACE=true
ENV DEVELOPER_MODE=true
ENV AUTO_START_LOOP=true
ENV OPERATION_LOOP_INTERVAL_MINUTES=30
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]
