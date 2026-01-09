import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.databases.base import Base

logger = logging.getLogger(__name__)

# Global engine and SessionLocal - created after app config is loaded
engine = None
SessionLocal = None


def init_mssql(app):
    """
    Initialize MSSQL database connection.
    Engine is created here (not at module level) to use app.config values.
    """
    global engine, SessionLocal
    
    # Get DATABASE_URI from app config (loaded from environment)
    database_uri = app.config.get('DATABASE_URI')
    if not database_uri:
        raise ValueError(
            "DATABASE_URI must be set in app configuration. "
            "Set DATABASE_URI environment variable in your .env file or environment."
        )
    
    logger.info(f"Initializing database connection to: {database_uri.split('@')[0]}@***")
    
    # Create engine with timeout and pool settings for MSSQL
    # pymssql connection parameters:
    # - timeout: connection timeout in seconds (default: 0 = no timeout)
    # - login_timeout: login timeout in seconds (default: 60)
    # Note: pymssql uses 'timeout' for connection and 'login_timeout' for authentication
    engine = create_engine(
        database_uri,
        connect_args={
            'timeout': 30,  # Connection timeout in seconds (increased for slow connections)
            'login_timeout': 30,  # Login timeout in seconds
        },
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_timeout=30,  # Timeout for getting connection from pool
        echo=False  # Set to True for SQL query logging
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Only create tables if AUTO_CREATE_TABLES is enabled (dev/test only)
    auto_create = os.environ.get('AUTO_CREATE_TABLES', 'False').lower() in ['true', '1']
    if auto_create:
        logger.warning("AUTO_CREATE_TABLES is enabled - creating database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    else:
        logger.info("AUTO_CREATE_TABLES is disabled - skipping table creation (use migrations in production)")