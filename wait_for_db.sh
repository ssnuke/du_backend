#!/bin/sh
set -e

echo "Waiting for PostgreSQL at $DB_HOST..."

until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec "$@"
