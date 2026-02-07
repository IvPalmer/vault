FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Set environment variables
ENV DJANGO_SETTINGS_MODULE=vault_project.settings
ENV PYTHONUNBUFFERED=1

# Create staticfiles directory and collect static files
RUN mkdir -p /app/staticfiles
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

# Dev: runserver, Prod: gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "vault_project.wsgi:application"]
