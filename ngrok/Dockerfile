# ngrok Docker service for webhook tunneling
FROM alpine:latest

# Install curl and download ngrok
RUN apk add --no-cache curl unzip && \
    curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz \
    -o ngrok.tgz && \
    tar -xzf ngrok.tgz && \
    mv ngrok /usr/local/bin/ && \
    rm ngrok.tgz

# Set working directory
WORKDIR /app

# Copy ngrok configuration
COPY ngrok.yml /root/.ngrok2/ngrok.yml

# Expose ngrok web interface port
EXPOSE 4040

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4040/api/tunnels || exit 1

# Default command - expose backend service
CMD ["ngrok", "http", "backend:8000", "--log=stdout"]
