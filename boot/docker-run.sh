#! /bin/bash

# Wait for the database to be ready
# /wait-for-db.sh db_service

# Activate the virtual environment
source /opt/venv/bin/activate

# Navigate to the project directory
cd /code

# Set host/port with fallback
RUN_PORT=${PORT:-8000}
RUN_HOST=${HOST:-0.0.0.0}

# Start Gunicorn with Uvicorn workers
gunicorn -k uvicorn.workers.UvicornWorker -b $RUN_HOST:$RUN_PORT main:app