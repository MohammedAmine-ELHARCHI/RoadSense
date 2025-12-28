FROM tensorflow/tensorflow:2.15.0

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only non-tensorflow requirements
COPY requirements.txt /tmp/requirements_all.txt

# Remove tensorflow line and install others
RUN grep -v "tensorflow" /tmp/requirements_all.txt | grep -v "tf-keras" | grep -v "tensorflow-io" > /tmp/requirements.txt && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm -rf /root/.cache/pip /tmp/requirements*.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/logs

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
