# Dockerfile
# Use a slim Python base image
FROM python:3.11-slim

# Prevent Python from writing pyc files or buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including postgresql-client
RUN apt-get update \
    && apt-get install -y postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Make sure the non-root user owns the application files
RUN chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Default command (Docker Compose will typically override this)
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]