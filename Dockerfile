
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p knowledge_base reports exports

# Expose port for Gradio
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME="0.0.0.0"

# Launch the application
CMD ["python3", "api/main.py"]
