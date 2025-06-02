#! /bin/bash

# Run the FastAPI project via the runtime script
# when the container starts
source /opt/venv/bin/activate

cd /code

RUN_PORT=${PORT:-8000}
RUN_HOST=${HOST:-0.0.0.0}

gunicorn -k uvicorn.workers.UvicornWorker -b $RUN_HOST:$RUN_PORT main:app