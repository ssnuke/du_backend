FROM python:3.13.2-slim-bullseye

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

RUN pip install --upgrade pip

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# OS dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libjpeg-dev \
    libcairo2 \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# App directory
WORKDIR /code
ENV PYTHONPATH=/code

# Install Python deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./src /code
# COPY ./src/main.py /code/main.py
# COPY ./src/alembic /code/alembic
# COPY ./src/alembic.ini /code/alembic.ini


# Startup script
COPY ./boot/docker-run.sh /opt/run.sh
RUN chmod +x /opt/run.sh

CMD ["/opt/run.sh"]
