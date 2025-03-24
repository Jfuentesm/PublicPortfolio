import logging
from sqlalchemy import create_engine
from core.database import Base, SessionLocal
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
from models.user import User
from models.job import Job

def create_or_update_admin_user():
    """
    Ensure the 'admin' user exists.
    If no user with username=admin, create one with default password 'password'.
    Otherwise, optionally update its password to ensure a consistent known credential.
    """
    db = SessionLocal()
    try:
        # Check for existing 'admin' user explicitly
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            logger.info("Admin user already exists.")
            # OPTIONAL: Force-update the password each time:
            # If you do NOT want to re-hash or overwrite the password, remove below lines.
            admin_user.hashed_password = get_password_hash("password")
            db.commit()
            logger.info("Admin password was updated/reset to default: 'password'.")
        else:
            # Create default admin user
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
    except Exception as e:
        logger.error(f"Error ensuring admin user: {e}")
        db.rollback()
    finally:
        db.close()

def initialize_database():
    """Initialize database by creating all tables, then ensuring 'admin' user exists."""
    try:
        logger.info(f"Initializing database at {settings.DATABASE_URL}")
        engine = create_engine(settings.DATABASE_URL)
        logger.info("Created database engine")
        
        logger.info("Creating all database tables")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Create or update the admin user
        create_or_update_admin_user()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting database initialization script")
    try:
        success = initialize_database()
        if success:
            logger.info("Database initialization completed successfully")
            sys.exit(0)
        else:
            logger.error("Database initialization failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unhandled exception during database initialization: {e}")
        sys.exit(1)