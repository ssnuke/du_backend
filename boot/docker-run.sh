#!/bin/bash
set -e

echo "🚀 Starting DU Backend (DEBUG MODE)"

source /opt/venv/bin/activate
export PYTHONPATH=/code
cd /code

echo "📁 Current directory:"
pwd

echo "📂 Listing /code:"
ls -la /code

echo "📂 Listing /code/alembic:"
ls -la /code/alembic || true

echo "📄 Showing alembic.ini:"
cat /code/alembic.ini || true

echo "🗄️ Running database migrations..."
alembic -c /code/alembic.ini upgrade head

echo "🚀 Starting application..."
gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8002} main:app
