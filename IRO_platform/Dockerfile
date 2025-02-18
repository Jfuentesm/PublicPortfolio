# Dockerfile - for building the Django and Celery containers
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files into the container
COPY . /app

# Expose port 8000 (though Docker Compose handles port mapping)
EXPOSE 8000

# Let 'compose.yaml' define the default command (gunicorn or Celery)