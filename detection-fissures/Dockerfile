FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    wget \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with legacy resolver to avoid pip crashes
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install --use-deprecated=legacy-resolver -r requirements.txt && \
    rm -rf /root/.cache/pip

# Install Detectron2 (optional - uncomment if needed)
# RUN pip3 install --no-cache-dir 'git+https://github.com/facebookresearch/detectron2.git'

# Download YOLOv8 pretrained weights (optional - speeds up first run)
RUN python3 -c "from ultralytics import YOLO; YOLO('yolov8m.pt')" || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/logs

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
