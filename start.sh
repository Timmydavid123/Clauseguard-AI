#!/usr/bin/env bash
set -euo pipefail

# send ALL script logs to Render stdout
exec 1> >(tee -a /proc/1/fd/1) 2> >(tee -a /proc/1/fd/2 >&2)

echo "Starting Ollama..."
export OLLAMA_HOST="0.0.0.0:11434"   # <--- important

# stream ollama logs to stdout (instead of hiding in /tmp)
ollama serve 2>&1 | sed -u 's/^/[ollama] /' &
OLLAMA_PID=$!

echo "Waiting for Ollama to be ready..."
for i in {1..90}; do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is up."
    break
  fi

  if ! kill -0 "$OLLAMA_PID" >/dev/null 2>&1; then
    echo "Ollama exited early."
    exit 1
  fi
  sleep 1
done

curl -fsS http://127.0.0.1:11434/api/tags >/dev/null

echo "Pulling model: ${OLLAMA_MODEL:-qwen2.5:3b-instruct}"
ollama pull "${OLLAMA_MODEL:-qwen2.5:3b-instruct}"

echo "Running migrations & collectstatic..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn on port ${PORT:-10000}..."
exec gunicorn clauseguard.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers 2 \
  --timeout 300