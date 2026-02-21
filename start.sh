#!/usr/bin/env bash
set -euo pipefail

echo "Starting Ollama..."
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
for i in {1..60}; do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is up."
    break
  fi

  # If ollama crashed, show logs and exit
  if ! kill -0 "$OLLAMA_PID" >/dev/null 2>&1; then
    echo "Ollama exited early. Last 200 lines of /tmp/ollama.log:"
    tail -n 200 /tmp/ollama.log || true
    exit 1
  fi

  sleep 1
done

# Final check
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama did not become ready in time. Last 200 lines of /tmp/ollama.log:"
  tail -n 200 /tmp/ollama.log || true
  exit 1
fi

echo "Pulling model: ${OLLAMA_MODEL:-qwen2.5:3b-instruct}"
ollama pull "${OLLAMA_MODEL:-qwen2.5:3b-instruct}"

echo "Running migrations & collectstatic..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn on port ${PORT:-10000}..."
exec gunicorn clauseguard.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers 2 \
  --timeout 300