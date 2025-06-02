#!/bin/bash
# wait-for-postgres.sh

set -e

host="$1"
shift
cmd="$@"

until pg_isready -h "$host" -p 5432 > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL at $host:5432..."
  sleep 1
done

>&2 echo "PostgreSQL is up — executing command"
exec $cmd
