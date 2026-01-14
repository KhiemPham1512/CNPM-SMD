import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from infrastructure.databases.base import Base

logger = logging.getLogger(__name__)

# Global engine and SessionLocal - created after app config is loaded
# SessionLocal is a scoped_session for thread-safety
engine = None
SessionLocal = None


def init_mssql(app):
    """
    Initialize MSSQL database connection.
    Engine is created here (not at module level) to use app.config values.
    Uses scoped_session for thread-safe session management.
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
    
    # Create thread-safe scoped session factory
    # scoped_session ensures each thread gets its own session instance
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    
    # Register teardown hook to remove session from thread-local storage
    @app.teardown_appcontext
    def remove_session(exception=None):
        """Remove session from thread-local storage after request completes."""
        SessionLocal.remove()
    
    # Only create tables if AUTO_CREATE_TABLES is enabled (dev/test only)
    # WARNING: This is NOT safe for production with existing data!
    # For demo/development: Use scripts/reset_db.py to rebuild database safely
    auto_create = os.environ.get('AUTO_CREATE_TABLES', 'False').lower() in ['true', '1']
    if auto_create:
        logger.warning("=" * 80)
        logger.warning("WARNING: AUTO_CREATE_TABLES is enabled!")
        logger.warning("This will create tables but will NOT handle schema changes or migrations.")
        logger.warning("For production: Use proper migration system (Alembic).")
        logger.warning("For demo/development: Use scripts/reset_db.py to rebuild database safely.")
        logger.warning("=" * 80)
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise RuntimeError(
                "Table creation failed. This may indicate schema conflicts. "
                "Use scripts/reset_db.py to rebuild database, or disable AUTO_CREATE_TABLES "
                "and use proper migrations."
            ) from e
    else:
        logger.info("AUTO_CREATE_TABLES is disabled - skipping table creation")
        logger.info("For demo setup: Run 'python scripts/reset_db.py' to create tables")
        logger.info("For production: Use proper migration system (Alembic)")