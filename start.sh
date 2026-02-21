#!/usr/bin/env bash
set -e

echo "Starting Ollama..."
ollama serve > /tmp/ollama.log 2>&1 &
sleep 2

echo "Pulling model: ${OLLAMA_MODEL}"
ollama pull "${OLLAMA_MODEL}"

echo "Running migrations & collectstatic..."
# python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn on port ${PORT:-10000}..."
gunicorn clauseguard.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 300