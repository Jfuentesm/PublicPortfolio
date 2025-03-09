#!/usr/bin/env bash

# run_local.sh
# Run this any time you need to rebuild or re-init the local environment.

set -e

echo "Stopping any running containers..."
docker compose down

echo "Removing postgres volume to ensure a fresh database..."
docker volume rm -f $(docker volume ls -q | grep postgres_data) || true

echo "Building Docker images..."
docker compose build

echo "Starting containers in the background..."
docker compose up -d

# Increase wait time from 5 to e.g. 15 seconds
WAIT_SECONDS=15
echo "Waiting $WAIT_SECONDS seconds for the web container to finish startup (extend this if needed)..."
sleep $WAIT_SECONDS

echo "===> Checking container statuses:"
docker compose ps

# OPTIONAL: a function to wait until the 'web' container is truly healthy (depends on if you have a healthcheck in docker-compose.yaml).
# This can be replaced by a direct check of logs or repeated 'docker compose ps' checks.

echo "===> Checking if 'web' container is still running..."
WEB_STATUS=$(docker compose ps --filter "status=running" --services | grep -w 'web' || true)
if [ -z "$WEB_STATUS" ]; then
  echo "ERROR: The 'web' container is not running after $WAIT_SECONDS seconds. Checking logs now..."
  docker compose logs web || true
  echo "Exiting script because 'web' service is not running."
  exit 1
fi

# Now we attempt to see if migrations are needed
echo "===> Checking if migrations are needed..."
# To confirm logs, we can do a quick "docker compose logs web --tail=50" to see any crash messages
# But let's proceed with the usual check:
if ! docker compose exec -T web python manage.py makemigrations --check; then
    echo "===> Migrations are needed. Creating migrations with default value for tenant field..."
    # Example of how you might handle interactive prompts:
    docker compose exec -T web bash -c "echo -e \"1\n1\n\" | python manage.py makemigrations assessments"
else
    echo "===> No migrations needed."
fi

echo "===> Running shared migrations..."
docker compose exec -T web python manage.py migrate_schemas --shared

echo "===> Creating or updating default tenant..."
docker compose exec -T web python manage.py init_tenant --name=default --domain=localhost

echo "===> Running tenant migrations..."
docker compose exec -T web python manage.py migrate_schemas --tenant

echo "===> Prepopulating sample data (2 tenants, each with 5 IROs fully assessed)..."
docker compose exec -T web python manage.py init_sample_data

echo "===> Synchronizing topics from existing IROs..."
docker compose exec -T web python manage.py sync_topics

echo "===> Setup completed. Tailing logs. Press Ctrl+C to stop."
docker compose logs -f