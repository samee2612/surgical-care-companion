"""
Database Connection and Session Management
SQLAlchemy engine and session configuration for PostgreSQL
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from backend.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables - with error handling"""
    try:
        # Import all models to ensure they're registered
        from backend.models.patient import Patient
        from backend.models.clinical_staff import ClinicalStaff
        from backend.models.call_session import CallSession
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.warning(f"Could not create database tables: {e}")
        logger.info("Server will start without database - start PostgreSQL later")
        # Don't raise exception - let server start anyway


def drop_tables():
    """Drop all database tables - USE WITH CAUTION!"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


async def check_db_connection():
    """Check database connection health."""
    try:
        from sqlalchemy import text
        db = SessionLocal()
        # Execute a simple query to test connection
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def init_db():
    """Initialize database with sample data."""
    try:
        from backend.models.patient import Patient
        from backend.models.clinical_staff import ClinicalStaff
        from backend.models.call_session import CallSession
        
        db = SessionLocal()
        
        # Check if we already have data
        if db.query(ClinicalStaff).first():
            logger.info("Database already initialized with data")
            db.close()
            return
            
        # Create sample clinical staff
        staff_data = [
            ClinicalStaff(
                name="Dr. Sarah Johnson",
                email="sarah.johnson@hospital.com",
                role="surgeon"
            ),
            ClinicalStaff(
                name="Nurse Mary Wilson",
                email="mary.wilson@hospital.com",
                role="nurse"
            ),
            ClinicalStaff(
                name="Care Coordinator Tom Brown",
                email="tom.brown@hospital.com",
                role="coordinator"
            )
        ]
        
        for staff in staff_data:
            db.add(staff)
        
        db.commit()
        logger.info("Database initialized with sample data")
        db.close()
        
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")
        # Don't raise exception - let server start anyway 