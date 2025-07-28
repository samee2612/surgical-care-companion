# surgicalcompanian/backend/Dockerfile
FROM python:3.11-slim

# Set working directory inside the container to /app.
# This is where your entire project will reside due to the volume mount.
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app" 

# Install system dependencies needed for psycopg2 (libpq-dev) and gcc for building some Python packages.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # ffmpeg \ # Uncomment if needed for audio processing later
    # libsndfile1 \ # Uncomment if needed for audio processing later
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt for the backend service from its location in the build context (./backend/)
# to the WORKDIR /app in the container.
COPY backend/requirements.txt requirements.txt # <<< CRUCIAL COPY PATH CHANGE
RUN pip install --no-cache-dir -r requirements.txt

# The 'COPY . .' command is now handled by the volume mount in docker-compose.yml.
# REMOVE: COPY . .

# Create necessary directories for runtime
RUN mkdir -p /app/logs /app/uploads

# Expose the port (matches what uvicorn will run on and docker-compose.yml)
EXPOSE 8000

# CMD is now overridden by docker-compose.yml 'command'
# CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]