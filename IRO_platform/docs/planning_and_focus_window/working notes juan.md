# need a launch script that integrates both the docker actions and the django migration
docker compose down
docker volume rm iro_platform_postgres_data
docker compose build
docker compose up


python manage.py makemigrations
python manage.py migrate_schemas --shared
python manage.py migrate_schemas --tenant


# tenants apps
With these settings in place, you can create a new tenants app containing your tenant models (TenantConfig, TenantDomain). Then, running python manage.py migrate_schemas --shared will apply migrations for SHARED_APPS to public, and python manage.py migrate_schemas --tenant will apply migrations for TENANT_APPS into each tenant’s schema.

# Clarify how to avoid conflict between sql init and django migrations



