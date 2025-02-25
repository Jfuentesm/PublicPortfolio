#!/usr/bin/env bash

# run_local.sh
# Run this any time you need to rebuild or re-init the local environment.

# Exit on error
set -e

echo "Building Docker images..."
docker compose down
docker compose build

echo "Starting containers in the background..."
docker compose up -d

echo "Tailing logs. Press Ctrl+C to stop."
docker compose logs -f