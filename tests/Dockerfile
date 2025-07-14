FROM python:3.11-slim

# Install system dependencies for testing
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy test requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://backend:8000/health || exit 1

# Default command
CMD ["python", "-m", "pytest", "-v", "--tb=short"]
