#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "Starting ClauseGuard Django Application"
echo "========================================="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

echo "Python version: $(python --version)"
echo "Pip packages:"
pip list | grep -E "Django|gunicorn|requests|pdfplumber"

echo "========================================="
echo "Environment variables:"
echo "PORT: ${PORT:-Not set}"
echo "OLLAMA_URL: ${OLLAMA_URL:-Not set}"
echo "OLLAMA_MODEL: ${OLLAMA_MODEL:-Not set}"

echo "========================================="
echo "Checking if manage.py exists:"
if [ -f "manage.py" ]; then
    echo "✅ manage.py found"
else
    echo "❌ manage.py NOT found!"
    echo "Searching for manage.py:"
    find / -name "manage.py" 2>/dev/null || echo "Not found"
fi

echo "========================================="
echo "Running Django checks..."
python manage.py check || {
    echo "⚠️  Django check failed but continuing..."
}

echo "Collecting static files..."
python manage.py collectstatic --noinput || {
    echo "⚠️  Collectstatic failed but continuing..."
}

echo "========================================="
echo "Starting Gunicorn..."
PORT="${PORT:-10000}"
echo "Binding to port: $PORT"

exec gunicorn clauseguard.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 2 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile - \
  --log-level info