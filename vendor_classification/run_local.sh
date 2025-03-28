#!/usr/bin/env bash

# ./run_local.sh [PORT]
# Run this script to setup and initialize the local development environment for the NAICS vendor classification system.
# Optional parameter:
#   PORT - The host port to use (default: 8001)

set -e

echo "Starting vendor classification setup..."

# Check if a port was provided as an argument, otherwise use default
WEB_PORT=${1:-8001}
echo "Using host port $WEB_PORT for the web service"

# ----- DOCKER CLEANUP SECTION -----
echo "Cleaning up Docker resources..."

# First attempt - normal docker compose down with logging
echo "Running docker compose down..."
docker compose down || echo "Warning: Initial docker compose down failed, will try additional cleanup"

# Check for any remaining containers using our network
NETWORK_CONTAINERS=$(docker network inspect vendor_classification_app-network -f '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null || echo "")
if [ -n "$NETWORK_CONTAINERS" ]; then
    echo "Containers still using the network: $NETWORK_CONTAINERS"
    echo "Forcefully stopping these containers..."
    for container in $NETWORK_CONTAINERS; do
        echo "Stopping container: $container"
        docker stop "$container" || echo "Failed to stop $container"
    done
    
    # Try docker compose down again
    echo "Running docker compose down again..."
    docker compose down || echo "Warning: Second docker compose down attempt failed"
fi

# As a last resort, try to force remove the network
echo "Checking if network still exists..."
if docker network ls | grep -q vendor_classification_app-network; then
    echo "Network still exists, attempting force removal..."
    docker network rm vendor_classification_app-network || echo "Warning: Failed to force remove network"
fi

# ----- REGULAR SETUP CONTINUES -----
# Create necessary directories
echo "Creating data directories..."
mkdir -p data/input data/output data/taxonomy data/logs

# **ADDED CHMOD IN RUN_LOCAL.SH**
echo "Setting permissions for log directory..."
chmod -R 777 data/logs

# Export the port as an environment variable
export WEB_PORT

echo "Removing postgres volume to ensure a fresh database..."
docker volume rm -f vendor_classification_postgres_data || true

echo "Building Docker images..."
docker compose build

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "Docker build failed. Please check the error messages above."
    exit 1
fi
echo "Docker build completed with exit code: $?"

echo "Starting containers in the background..."
docker compose up -d

# Check if containers started successfully
if [ $? -ne 0 ]; then
  echo "There was an error starting the containers. Please check the Docker logs."
  exit 1
fi

WAIT_SECONDS=15
echo "Waiting $WAIT_SECONDS seconds for containers to start..."
sleep $WAIT_SECONDS

echo "===> Checking container statuses:"
docker compose ps

# Check if web container is running
WEB_CONTAINER=$(docker compose ps -q web)
if [ -z "$WEB_CONTAINER" ]; then
    echo "Web container failed to start! Check logs with: docker compose logs web"
    exit 1
fi

echo "===> Checking web container logs:"
docker compose logs web --tail 20

echo "===> Testing web service connectivity:"
curl -v http://localhost:$WEB_PORT/health || echo "Warning: Could not connect to web service health endpoint!"

echo "===> Setup completed. The system is now ready to use."
echo "Access the web interface at: http://localhost:$WEB_PORT"
echo "Login with username: admin, password: password"
echo "PostgreSQL is available on port 5433 instead of the default 5432"
echo ""
echo "Press Enter to show logs, or Ctrl+C to exit."
read -r
docker compose logs -f