#!/bin/bash
set -e

echo "Starting Ollama server in background..."
/bin/ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to start..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama is up!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Check if Ollama is really running
if ! kill -0 $OLLAMA_PID 2>/dev/null; then
    echo "❌ Ollama failed to start"
    exit 1
fi

# Pull the model
echo "📦 Pulling model: ${OLLAMA_MODEL}"
/bin/ollama pull "${OLLAMA_MODEL}"

echo "✅ Ollama ready! Model ${OLLAMA_MODEL} is loaded"

# Keep container running and follow logs
wait $OLLAMA_PID