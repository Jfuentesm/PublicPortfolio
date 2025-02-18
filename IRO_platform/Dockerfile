# Start with an official Python image
FROM python:3.10-slim

# Create a working directory in the container
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into /app
COPY . /app/

# Expose port 8000 (not strictly necessary if you rely on Docker Compose)
EXPOSE 8000

# By default, just start a bash shell; 
# actual command is overridden by `command:` in docker-compose
CMD ["/bin/bash"]