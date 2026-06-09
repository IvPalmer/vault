#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
# gthread workers: a blocking request (Drive byte-range fetch, video stream)
# holds one thread, not a whole worker — so streaming media can't starve the
# 4 workers and stall the rest of the app. Longer timeout for long streams.
exec gunicorn --bind 0.0.0.0:8000 \
  --worker-class gthread --workers 4 --threads 8 \
  --timeout 300 --graceful-timeout 30 \
  vault_project.wsgi:application
