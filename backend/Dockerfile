# Pinned Python version matching pyproject.toml (requires-python = ">=3.12")
FROM python:3.12.9-slim-bookworm

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install minimal OS dependencies for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install project dependencies from pyproject.toml with layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python -c "import tomllib; c = tomllib.load(open('pyproject.toml', 'rb')); open('/tmp/requirements.txt', 'w').write('\n'.join(c['project']['dependencies']))" && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Copy application source code
COPY . .
RUN pip install --no-cache-dir --no-deps .

# Collect static assets at build time (independent of database connection)
RUN SECRET_KEY="build-phase-dummy-secret-key-not-for-runtime" \
    DATABASE_URL="postgres://dummy:dummy@localhost:5432/dummy" \
    ALLOWED_HOSTS="*" \
    DJANGO_SETTINGS_MODULE="config.settings.base" \
    python manage.py collectstatic --noinput

# Create non-root system user for least-privilege runtime security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Production-ready Gunicorn entrypoint
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 2 --timeout 60 --access-logfile - --error-logfile -"]
