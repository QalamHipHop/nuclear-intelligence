# Nuclear Intelligence v4.0 - HF Space Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY app.py .

# Environment
ENV GRADIO_PORT=7860
ENV HF_SPACE=true
ENV DEVELOPER_MODE=true
ENV AUTO_START_LOOP=false

# Expose port
EXPOSE 7860

# Run
CMD ["python", "app.py"]