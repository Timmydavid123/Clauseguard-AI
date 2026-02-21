#!/bin/bash
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to start..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama is up!"
        break
    fi
    sleep 1
done

# Pull the model in background
echo "Pulling model: ${OLLAMA_MODEL}"
/pull-model.sh "${OLLAMA_MODEL}" &

# Keep container running
wait $OLLAMA_PID