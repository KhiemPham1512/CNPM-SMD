"""
Database session management using Flask request context.

This module provides centralized session management to avoid
creating multiple sessions per request.
"""
from flask import g
from dependency_container import get_session_local


def get_db_session():
    """
    Get database session from Flask request context.
    Creates session if not exists, reuses if already created.
    
    Session is automatically closed via teardown_appcontext.
    """
    if 'db' not in g:
        SessionLocal = get_session_local()
        g.db = SessionLocal()
    return g.db


def close_db_session(error=None):
    """
    Close database session in Flask teardown.
    Called automatically by Flask after request completes.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
