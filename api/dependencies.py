"""
FastAPI dependencies for database connections and common utilities
"""
from typing import Generator
from sqlalchemy import text
from etl.database import db


def get_db_connection() -> Generator:
    """
    FastAPI dependency that provides a SQLAlchemy database connection.
    Yields a connection that automatically commits and closes.
    """
    # Ensure database is connected
    if not db.engine:
        db.connect()

    conn = db.engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(query: str, params: dict = None):
    """
    Execute a query and return results as list of dictionaries.
    Helper function for routers.
    """
    if not db.engine:
        db.connect()

    with db.engine.connect() as conn:
        if params:
            result = conn.execute(text(query), params)
        else:
            result = conn.execute(text(query))

        # Convert to list of dicts
        rows = result.fetchall()
        if rows:
            # Get column names from result
            columns = result.keys()
            return [dict(zip(columns, row)) for row in rows]
        return []
