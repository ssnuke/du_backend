#!/bin/sh
# wait-for-db.sh

set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 -U "$POSTGRES_USER"; do
  echo "Waiting for Postgres at $host..."
  sleep 1
done

exec $cmd
