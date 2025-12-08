FROM python:3.10-slim

WORKDIR /app

# Install dependencies with legacy resolver to avoid pip crashes
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --use-deprecated=legacy-resolver -r requirements.txt && \
    rm -rf /root/.cache/pip

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/logs

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
