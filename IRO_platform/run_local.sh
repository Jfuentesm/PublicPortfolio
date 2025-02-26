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

# Wait a few seconds to ensure the web container is fully started
echo "Waiting for the web container to finish startup..."
sleep 5

echo "Running shared migrations..."
docker compose exec -T web python manage.py migrate_schemas --shared

echo "Creating or updating default tenant..."
docker compose exec -T web python manage.py init_tenant --name=default --domain=localhost

echo "Running tenant migrations..."
docker compose exec -T web python manage.py migrate_schemas --tenant

echo "Prepopulating sample data (2 tenants, each with 5 IROs fully assessed)..."
docker compose exec -T web python manage.py init_sample_data

echo "Tailing logs. Press Ctrl+C to stop."
docker compose logs -f