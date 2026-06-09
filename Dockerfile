FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_enhanced.txt .
RUN pip3 install --no-cache-dir -r requirements_enhanced.txt

COPY . .

# Expose ports for FastAPI and Gradio
EXPOSE 8000
EXPOSE 7860

# Command to run the Gradio UI by default
CMD ["python3", "app_enhanced.py"]
