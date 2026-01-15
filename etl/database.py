"""
Database connection and session management.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import logging

from etl.config import config

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self):
        self.engine = None
        self.Session = None

    def connect(self, use_pool: bool = None):
        """
        Create database engine and session factory.

        Args:
            use_pool: If True, use connection pooling (better for API).
                     If False, use NullPool (better for ETL batch jobs).
                     If None, auto-detect based on environment.
        """
        try:
            # Auto-detect: use pooling in API mode, NullPool for ETL
            if use_pool is None:
                # Check if we're running in API context (e.g., via uvicorn)
                use_pool = os.environ.get('API_MODE', '').lower() == 'true' or \
                           'uvicorn' in os.environ.get('SERVER_SOFTWARE', '').lower()

            if use_pool:
                # Connection pooling for API - keeps connections alive
                self.engine = create_engine(
                    config.get_database_url(),
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,  # Verify connections before use
                    pool_recycle=300,  # Recycle connections after 5 minutes
                    echo=False
                )
                logger.info("Database engine created with connection pooling")
            else:
                # No pooling for ETL batch jobs
                self.engine = create_engine(
                    config.get_database_url(),
                    poolclass=NullPool,
                    echo=False
                )
                logger.info("Database engine created without connection pooling (ETL mode)")

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version FROM schema_version"))
                version = result.scalar()
                logger.info(f"Connected to database (schema version: {version})")

            # Create session factory
            self.Session = sessionmaker(bind=self.engine)

            return True

        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def get_session(self):
        """Get a new database session"""
        if not self.Session:
            self.connect()
        return self.Session()

    def execute(self, query, params=None):
        """Execute a raw SQL query"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            conn.commit()
            return result

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Create singleton instance
db = Database()
