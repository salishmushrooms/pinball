"""
Database connection and session management.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import logging

from etl.config import config

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self):
        self.engine = None
        self.Session = None

    def connect(self):
        """Create database engine and session factory"""
        try:
            self.engine = create_engine(
                config.get_database_url(),
                poolclass=NullPool,  # No connection pooling for ETL
                echo=False  # Set to True for SQL debug logging
            )

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
