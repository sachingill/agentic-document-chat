# Dockerfile for containerized deployment (Fly.io, Railway, etc.)
# Multi-stage build for optimized image size

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
# Note: In production, you'll typically run one service per container
EXPOSE 8000 8001 8501

# Default command (override in docker-compose or platform config)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

