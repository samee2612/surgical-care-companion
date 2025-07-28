# surgicalcompanian/backend/Dockerfile
FROM python:3.11-slim

# Set working directory inside the container to /app.
# This is where your entire project will reside.
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Set Python path to include the /app directory itself.
# This makes imports like 'from backend.services.database_manager import DatabaseManager' work.
ENV PYTHONPATH="/app"

# Install system dependencies needed for psycopg2 (libpq-dev) and gcc for building some Python packages.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    # ffmpeg \ # Uncomment if needed for audio processing later (e.g., for Whisper/CoquiTTS)
    # libsndfile1 \ # Uncomment if needed for audio processing later
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt for the backend service.
# It's at surgicalcompanian/backend/requirements.txt relative to the build context (root of your project).
# We copy it to /app/requirements.txt in the container.
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL remaining application code from your project root into /app in the container.
# This will copy 'backend/', 'scripts/', 'docs/', 'migrations/', etc. into /app.
COPY . .

# Create necessary directories for runtime
RUN mkdir -p /app/logs /app/uploads

# Expose the port (matches what uvicorn will run on and docker-compose.yml)
EXPOSE 8000

# Default command (this is usually overridden by docker-compose.yml 'command')
# It runs the FastAPI app located at /app/backend/main.py
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]