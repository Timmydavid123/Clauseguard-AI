#!/usr/bin/env bash
set -euo pipefail

echo "Collectstatic..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn on port ${PORT:-10000}..."
gunicorn clauseguard.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers 2 \
  --timeout 300 &
GUNICORN_PID=$!

echo "Starting Ollama (localhost only)..."
export OLLAMA_HOST="127.0.0.1:11434"
ollama serve > /tmp/ollama.log 2>&1 &
OLLAMA_PID=$!

echo "Waiting for Ollama..."
for i in {1..120}; do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama is up."
    break
  fi
  if ! kill -0 "$OLLAMA_PID" >/dev/null 2>&1; then
    echo "Ollama exited early. Last 200 lines:"
    tail -n 200 /tmp/ollama.log || true
    kill "$GUNICORN_PID" || true
    exit 1
  fi
  sleep 1
done

# OPTIONAL: pull model only if missing (prevents re-pulling)
MODEL="${OLLAMA_MODEL:-qwen2.5:3b-instruct}"
if ! curl -fsS http://127.0.0.1:11434/api/tags | grep -q "\"name\":\"$MODEL\""; then
  echo "Pulling model: $MODEL"
  ollama pull "$MODEL" >> /tmp/ollama.log 2>&1
else
  echo "Model already present: $MODEL"
fi

echo "All services up. Tailing..."
wait -n "$GUNICORN_PID" "$OLLAMA_PID"
echo "A process exited. Dumping ollama log:"
tail -n 200 /tmp/ollama.log || true
exit 1