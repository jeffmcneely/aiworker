FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables with defaults
ENV LOG_LEVEL=INFO
ENV COMFY_HOST=comfyui
ENV COMFY_PORT=8188
ENV POLL_INTERVAL=2
ENV OUTPUT_FOLDER=/app/output

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://${COMFY_HOST}:${COMFY_PORT}/system_stats || exit 1

# Run the application
CMD ["python", "comfy-watcher.py"]
