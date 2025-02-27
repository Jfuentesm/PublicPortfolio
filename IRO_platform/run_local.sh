#!/usr/bin/env bash

# run_local.sh
# Run this any time you need to rebuild or re-init the local environment.

# Exit on error
set -e

echo "Stopping any running containers..."
docker compose down

echo "Removing postgres volume to ensure a fresh database..."
docker volume rm -f $(docker volume ls -q | grep postgres_data) || true

echo "Building Docker images..."
docker compose build

echo "Starting containers in the background..."
docker compose up -d

# Wait a few seconds to ensure the web container is fully started
echo "Waiting for the web container to finish startup..."
sleep 5

# First check if migrations are needed
echo "Checking if migrations are needed..."
if ! docker compose exec -T web python manage.py makemigrations --check; then
    echo "Migrations are needed. Creating migrations with default value for tenant field..."
    # Simulate selecting option 1 (one-off default) and providing default value 1
    docker compose exec -T web bash -c "echo -e \"1\n1\n\" | python manage.py makemigrations assessments"
else
    echo "No migrations needed."
fi

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
