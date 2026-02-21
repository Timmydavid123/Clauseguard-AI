#!/bin/bash
MODEL=${1:-qwen2.5:3b-instruct}

# Wait a bit for Ollama to be fully ready
sleep 5

# Check if model exists
if ! curl -s http://localhost:11434/api/tags | grep -q "\"name\":\"$MODEL\""; then
    echo "Pulling model: $MODEL"
    ollama pull "$MODEL"
else
    echo "Model $MODEL already exists"
fi