#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "import socket; s = socket.create_connection(('db', 5432), timeout=2)" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec "$@"
