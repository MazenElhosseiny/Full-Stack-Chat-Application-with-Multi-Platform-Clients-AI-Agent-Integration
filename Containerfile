FROM docker.io/library/python:3.12-slim

# Install Ollama (zstd is required by the Ollama installer — its package
# switched to zstd compression; without it the install aborts mid-build)
RUN apt-get update && apt-get install -y curl zstd && \
    curl -fsSL https://ollama.com/install.sh | sh && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir openai requests

WORKDIR /app
COPY harness.py .

EXPOSE 9090

# Start Ollama, wait until the API is ready, pull the model only if missing,
# then start the harness.
#
# Ollama caches models in /root/.ollama. Mount a volume there so you don't
# re-download ~2GB every time you recreate the container (Stage 2/3):
#   podman run -v ollama-models:/root/.ollama ...
CMD ollama serve & \
    until ollama list > /dev/null 2>&1; do sleep 1; done && \
    (ollama list | grep -q llama3.2:3b || ollama pull llama3.2:3b) && \
    python harness.py
