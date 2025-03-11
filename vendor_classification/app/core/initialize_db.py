import logging
from sqlalchemy import create_engine
from core.database import Base
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

def create_default_user():
    """Create a default admin user if no users exist."""
    logger.info("Checking for existing users...")
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Check if any users exist
        user_count = db.query(User).count()
        logger.info(f"Found {user_count} existing users")
        
        if user_count == 0:
            # Create default admin user
            default_user = User(
                id=str(uuid.uuid4()),
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=get_password_hash("password"),
                is_active=True,
                is_superuser=True
            )
            
            db.add(default_user)
            db.commit()
            logger.info("Created default admin user: admin / password")
        else:
            logger.info("Users already exist, skipping default user creation")
    
    except Exception as e:
        logger.error(f"Error creating default user: {e}")
        db.rollback()
    finally:
        db.close()

def initialize_database():
    """Initialize database by creating all tables."""
    try:
        logger.info(f"Initializing database at {settings.DATABASE_URL}")
        engine = create_engine(settings.DATABASE_URL)
        logger.info("Created database engine")
        
        logger.info("Creating all database tables")
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Create default user
        create_default_user()
        
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