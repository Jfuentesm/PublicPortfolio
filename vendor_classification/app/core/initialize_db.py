# --- file path='app/core/initialize_db.py' ---
import logging
from sqlalchemy import create_engine, inspect as sql_inspect # Added inspect
from sqlalchemy.exc import SQLAlchemyError # Added for specific exception handling
from core.database import Base, SessionLocal, engine # Import engine directly
from core.config import settings
import sys
import uuid
from api.auth import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vendor_classification.db_init")

# Import all models to ensure they're registered with SQLAlchemy
logger.info("Importing models for database initialization")
try:
    from models.user import User
    from models.job import Job
    # Import other models here if they exist
    logger.info("Models imported successfully.")
except ImportError as e:
    logger.critical(f"Failed to import models for DB initialization: {e}", exc_info=True)
    sys.exit(1) # Exit if models can't be imported

def create_or_update_admin_user():
    """
    Ensure the 'admin' user exists.
    If no user with username=admin, create one with default password 'password'.
    Otherwise, optionally update its password to ensure a consistent known credential.
    """
    db = None # Initialize db to None
    try:
        db = SessionLocal()
        logger.info("Checking for existing admin user...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            logger.info("Admin user already exists.")
            # OPTIONAL: Force-update the password each time:
            # If you do NOT want to re-hash or overwrite the password, remove below lines.
            try:
                logger.info("Attempting to update admin password to default 'password'...")
                admin_user.hashed_password = get_password_hash("password")
                db.commit()
                logger.info("Admin password was updated/reset to default: 'password'.")
            except Exception as hash_err:
                logger.error(f"Failed to update admin password: {hash_err}", exc_info=True)
                db.rollback() # Rollback password change on error
        else:
            logger.info("Admin user not found, creating default admin user...")
            admin_user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=get_password_hash("password"),
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user: admin / password")
    except SQLAlchemyError as e: # Catch specific DB errors
        logger.error(f"Database error during admin user check/creation: {e}", exc_info=True)
        if db: db.rollback()
    except Exception as e: # Catch other errors like hashing
        logger.error(f"Unexpected error ensuring admin user: {e}", exc_info=True)
        if db: db.rollback()
    finally:
        if db:
            db.close()
            logger.info("Admin user check/creation DB session closed.")

    # --- Add sample users user_1 and user_2 ---
    sample_users = [
        {
            "username": "user_1",
            "email": "user_1@example.com",
            "full_name": "User One",
            "password": "user_1",
            "is_superuser": False
        },
        {
            "username": "user_2",
            "email": "user_2@example.com",
            "full_name": "User Two",
            "password": "user_2",
            "is_superuser": False
        }
    ]
    db = None
    try:
        db = SessionLocal()
        for user in sample_users:
            existing_user = db.query(User).filter(User.username == user["username"]).first()
            if existing_user:
                logger.info(f"Sample user '{user['username']}' already exists.")
                # Optionally update password to default
                try:
                    logger.info(f"Attempting to update password for '{user['username']}' to default '{user['password']}'...")
                    existing_user.hashed_password = get_password_hash(user["password"])
                    db.commit()
                    logger.info(f"Password for '{user['username']}' was updated/reset to default: '{user['password']}'.")
                except Exception as hash_err:
                    logger.error(f"Failed to update password for '{user['username']}': {hash_err}", exc_info=True)
                    db.rollback()
            else:
                logger.info(f"Sample user '{user['username']}' not found, creating...")
                new_user = User(
                    id=str(uuid.uuid4()),
                    username=user["username"],
                    email=user["email"],
                    full_name=user["full_name"],
                    hashed_password=get_password_hash(user["password"]),
                    is_active=True,
                    is_superuser=user["is_superuser"]
                )
                db.add(new_user)
                db.commit()
                logger.info(f"Created sample user: {user['username']} / {user['password']}")
    except SQLAlchemyError as e:
        logger.error(f"Database error during sample user check/creation: {e}", exc_info=True)
        if db: db.rollback()
    except Exception as e:
        logger.error(f"Unexpected error ensuring sample users: {e}", exc_info=True)
        if db: db.rollback()
    finally:
        if db:
            db.close()
            logger.info("Sample user check/creation DB session closed.")

def initialize_database():
    """Initialize database by creating all tables, then ensuring 'admin' user exists."""
    max_retries = 5
    retry_delay = 5 # seconds
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting database initialization (Attempt {attempt + 1}/{max_retries})...")
            # Use the imported engine
            logger.info(f"Using database engine for URL: {settings.DATABASE_URL.split('@')[-1]}")

            # Check connection before creating tables
            with engine.connect() as connection:
                logger.info("Successfully connected to the database.")

            logger.info("Inspecting existing tables...")
            inspector = sql_inspect(engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables found: {existing_tables}")

            logger.info("Attempting to create all tables defined in Base.metadata...")
            # Log the tables Base knows about
            logger.info(f"Base.metadata knows about tables: {list(Base.metadata.tables.keys())}")
            Base.metadata.create_all(engine)
            logger.info("Base.metadata.create_all(engine) executed successfully.")

            # Verify tables were created
            logger.info("Re-inspecting tables after create_all...")
            inspector = sql_inspect(engine) # Re-inspect
            new_existing_tables = inspector.get_table_names()
            logger.info(f"Tables found after create_all: {new_existing_tables}")

            # Specifically check for 'users' and 'jobs' tables
            if 'users' not in new_existing_tables:
                logger.error("'users' table NOT FOUND after create_all call!")
            else:
                logger.info("'users' table found after create_all call.")
            if 'jobs' not in new_existing_tables:
                logger.warning("'jobs' table NOT FOUND after create_all call!") # Maybe optional?
            else:
                logger.info("'jobs' table found after create_all call.")

            # Create or update the admin user
            create_or_update_admin_user()

            logger.info("Database initialization appears successful.")
            return True # Success

        except SQLAlchemyError as e:
            logger.error(f"Database connection or table creation error on attempt {attempt + 1}: {e}", exc_info=False) # Don't need full trace every retry
            if attempt + 1 == max_retries:
                logger.critical("Max retries reached. Database initialization failed.", exc_info=True)
                raise # Raise the last exception
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error during database initialization attempt {attempt + 1}: {e}", exc_info=True)
            # Decide if retry makes sense for unexpected errors, maybe not
            raise # Re-raise immediately for unexpected errors

    logger.error("Database initialization failed after all retries.")
    return False # Should not be reached if exceptions are raised

if __name__ == "__main__":
    import time # Import time for retries
    logger.info("Starting database initialization script directly...")
    try:
        success = initialize_database()
        if success:
            logger.info("Database initialization script completed successfully.")
            sys.exit(0)
        else:
            logger.error("Database initialization script failed.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled exception during database initialization script: {e}", exc_info=True)
        sys.exit(1)