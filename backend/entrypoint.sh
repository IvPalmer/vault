#!/bin/sh
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 vault_project.wsgi:application
