"""
Database session management using Flask request context.

This module provides centralized session management to avoid
creating multiple sessions per request.
Uses scoped_session for thread-safety.
"""
from flask import g
from dependency_container import get_session_local


def get_db_session():
    """
    Get database session from Flask request context.
    Creates session if not exists, reuses if already created.
    
    Session is automatically removed from thread-local storage via teardown_appcontext.
    With scoped_session, SessionLocal() returns the thread-local session instance.
    """
    if 'db' not in g:
        SessionLocal = get_session_local()
        g.db = SessionLocal()
    return g.db


def close_db_session(error=None):
    """
    Close database session in Flask teardown.
    Called automatically by Flask after request completes.
    
    Note: With scoped_session, SessionLocal.remove() is called in mssql.py teardown hook.
    This function ensures session is properly cleaned up even if exceptions occur.
    """
    db = g.pop('db', None)
    if db:
        try:
            # Rollback if there was an error and session is still active
            if error is not None:
                db.rollback()
        except Exception as e:
            # Log but don't raise - we're in teardown
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error during session cleanup: {e}")
    # scoped_session cleanup is handled by SessionLocal.remove() in mssql.py
    # This ensures g.db is cleared to avoid stale references
