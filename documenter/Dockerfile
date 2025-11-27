# Doctown Agent Runtime
# This container runs an AI agent in a secure sandbox to process .docpack files

FROM python:3.12-slim

# Install system dependencies for common tools
RUN apt-get update && apt-get install -y \
    ripgrep \
    git \
    tree \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./

# Create workspace directory where .docpack will be mounted
RUN mkdir -p /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_PATH=/workspace

# Run as non-root user for security
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app /workspace
USER agent

# The entrypoint will run the agent orchestrator
CMD ["python", "main.py"]
