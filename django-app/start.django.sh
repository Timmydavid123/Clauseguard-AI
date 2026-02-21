#!/usr/bin/env bash
set -euo pipefail

echo "Collectstatic..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn on port ${PORT:-10000}..."
exec gunicorn clauseguard.wsgi:application \
  --bind 0.0.0.0:${PORT:-10000} \
  --workers 2 \
  --timeout 300