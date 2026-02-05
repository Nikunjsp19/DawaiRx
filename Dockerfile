# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for pandas, reportlab, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and outputs (Azure will use /tmp or mounted volumes)
RUN mkdir -p /app/uploads /app/outputs /tmp/uploads /tmp/outputs

# Expose port (Azure will override with PORT env var)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check - use /health endpoint (lightweight, no MongoDB dependency)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Copy and use startup script (helps capture errors in Azure logs)
COPY scripts/start.sh /app/scripts/start.sh
RUN chmod +x /app/scripts/start.sh

# Run the application
# Azure provides PORT env var, the web command will read it automatically
# Use 0.0.0.0 to accept connections from outside the container
CMD ["/app/scripts/start.sh"]

