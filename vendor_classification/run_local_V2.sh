#!/usr/bin/env bash

# ./run_local_V2.sh [PORT]
# Run this script to setup and initialize the local development environment
# for the NAICS vendor classification system.
# WARNING: THIS VERSION *REMOVES* THE DATABASE VOLUME ON EACH RUN,
#          CLEARING ALL PREVIOUS DATA.
# Optional parameter:
#   PORT - The host port to use (default: 8001)

set -e

echo "Starting vendor classification setup (DATABASE WILL BE RESET)..." # Updated message

# Check if a port was provided as an argument, otherwise use default
WEB_PORT=${1:-8001}
echo "Using host port $WEB_PORT for the web service"

# ----- DOCKER CLEANUP SECTION (MODIFIED TO REMOVE DB VOLUME) -----
echo "Cleaning up Docker resources (Containers, Networks, and DB Volume)..."
# Use docker compose command based on version (v1 or v2+)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    NETWORK_NAME="vendor_classification_app-network" # Default network name for v2+
    VOLUME_NAME="vendor_classification_postgres_data" # Default volume name for v2+
elif docker-compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    PROJECT_NAME=$(basename "$PWD" | sed 's/[^a-zA-Z0-9]//g') # Simple project name from dir
    NETWORK_NAME="${PROJECT_NAME}_app-network" # Common pattern for v1
    VOLUME_NAME="${PROJECT_NAME}_postgres_data" # Common pattern for v1
else
    echo "ERROR: Neither 'docker compose' (v2+) nor 'docker-compose' (v1) found. Please install Docker Compose."
    exit 1
fi
echo "Using compose command: '$COMPOSE_CMD'"
echo "Database volume name expected: '$VOLUME_NAME' (will be REMOVED)"

# Bring down containers and networks, AND remove volumes (-v flag ADDED)
$COMPOSE_CMD down --remove-orphans -v || echo "Warning: docker compose down failed, continuing cleanup..."

# Force remove network if it persists (compose down should handle this, but just in case)
if docker network inspect $NETWORK_NAME >/dev/null 2>&1; then
    echo "Network '$NETWORK_NAME' still exists, attempting force removal..."
    docker network rm -f $NETWORK_NAME || echo "Warning: Failed to force remove network '$NETWORK_NAME'"
else
    echo "Network '$NETWORK_NAME' does not exist or was removed."
fi

# Explicitly remove the database volume (compose down -v should handle this, but belt-and-suspenders)
echo "Attempting explicit removal of volume '$VOLUME_NAME'..."
docker volume rm -f $VOLUME_NAME || echo "Warning: Failed to remove volume '$VOLUME_NAME' or it didn't exist."
echo "Docker container/network/volume cleanup attempt finished."
# ----- END DOCKER CLEANUP -----

# Create necessary directories
echo "Creating data directories..."
mkdir -p data/input data/output data/taxonomy data/logs # Ensures structure exists

# --- ADDED: Clear logs directory ---
echo "Clearing previous contents of data/logs/ ..."
# Remove the directory and its contents, then recreate it to ensure it's empty
# Using rm -rf followed by mkdir -p is robust
rm -rf data/logs && mkdir -p data/logs || { echo "ERROR: Failed to clear and recreate data/logs directory. Check permissions."; exit 1; }
# --- END: Clear logs directory ---

# Set permissions for log directory (needs to happen AFTER recreation)
echo "Setting permissions for log directory..."
chmod -R 777 data/logs || echo "Warning: Could not set permissions on data/logs. Logging might fail if user IDs mismatch."

# Export the port as an environment variable
export WEB_PORT

# --- ADDED LOGGING ---
echo "Checking for frontend build files locally before Docker build:"
ls -l frontend/vue_frontend/package.json || { echo "ERROR: frontend/vue_frontend/package.json not found locally! Cannot build frontend."; exit 1; }
ls -l frontend/vue_frontend/vite.config.js || ls -l frontend/vue_frontend/vite.config.ts || { echo "WARNING: vite.config file not found locally! Frontend build might fail."; }
# --- END ADDED LOGGING ---

echo "Building Docker images (this will include the Vue frontend build)..."
# Use the detected compose command
$COMPOSE_CMD build --no-cache web # Rebuild web to ensure latest code
$COMPOSE_CMD build worker db redis

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "Docker build failed. Please check the error messages above."
    exit 1
fi
echo "Docker build completed successfully."

echo "Starting containers in the background..."
# Use the detected compose command
$COMPOSE_CMD up -d

# Check if containers started successfully
if [ $? -ne 0 ]; then
  echo "There was an error starting the containers. Please check the Docker logs."
  exit 1
fi

WAIT_SECONDS=15 # Keep wait time as DB init might take a moment
echo "Waiting $WAIT_SECONDS seconds for containers to start and DB to initialize..."
sleep $WAIT_SECONDS

echo "===> Checking container statuses:"
$COMPOSE_CMD ps

# Check if web container is running
WEB_CONTAINER_ID=$($COMPOSE_CMD ps -q web)
if [ -z "$WEB_CONTAINER_ID" ]; then
    echo "Web container failed to start! Check logs with: $COMPOSE_CMD logs web"
    exit 1
else
    echo "Web container ($WEB_CONTAINER_ID) appears to be running."
fi

echo "===> Checking web container logs (last 30 lines):"
$COMPOSE_CMD logs web --tail 30

echo "===> Testing web service connectivity (Health Check):"
retry_count=0
max_retries=5
until curl -f -s -o /dev/null "http://localhost:$WEB_PORT/health"; do
    retry_count=$((retry_count+1))
    if [ $retry_count -ge $max_retries ]; then
        echo "Warning: Could not connect to web service health endpoint (http://localhost:$WEB_PORT/health) after $max_retries attempts! Check logs."
        break
    fi
    echo "Health check failed, retrying in 5 seconds... ($retry_count/$max_retries)"
    sleep 5
done
if [ $retry_count -lt $max_retries ]; then
    echo "Health check successful!"
fi


echo ""
echo "===> Setup completed (Database RESET, Logs Cleared)." # Updated message
echo "Access the web interface (built Vue app) at: http://localhost:$WEB_PORT"
echo "Login with username: admin, password: password"
echo "PostgreSQL is available on host port 5433"
echo "Database data in volume '$VOLUME_NAME' was REMOVED and recreated." # Updated message
echo "Log directory 'data/logs' was cleared before this run."
echo ""
echo "*** Frontend Development Note ***"
echo "The frontend served by this container is the *built* version."
echo "For frontend development, run the Vue dev server separately:"
echo "  cd frontend/vue_frontend"
echo "  npm install  # If needed"
echo "  npm run dev"
echo "Then access the dev server (usually http://localhost:5173 or similar)."
echo "The dev server should proxy API requests to http://localhost:$WEB_PORT (configure in frontend/vue_frontend/vite.config.js/ts if needed)."
echo "*******************************"
echo ""
echo "Press Enter to show continuous logs, or Ctrl+C to exit."
read -r
$COMPOSE_CMD logs -f