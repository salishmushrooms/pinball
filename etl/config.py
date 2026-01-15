"""
Configuration module for ETL pipeline.
Loads database connection details from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Config:
    """ETL Configuration"""

    # Database configuration
    # Prefer LOCAL_DATABASE_URL for local development, fall back to DATABASE_URL (which might be remote)
    DATABASE_URL = os.getenv(
        'LOCAL_DATABASE_URL',
        os.getenv('DATABASE_URL', 'postgresql://mnp_user:changeme@localhost:5432/mnp_analyzer')
    )
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'mnp_analyzer')
    DB_USER = os.getenv('DB_USER', 'mnp_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'changeme')

    # Data paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_PATH = PROJECT_ROOT / 'mnp-data-archive'
    MACHINE_VARIATIONS_FILE = PROJECT_ROOT / 'machine_variations.json'

    # ETL settings
    BATCH_SIZE = 1000  # Number of records to insert at once

    @classmethod
    def get_database_url(cls):
        """Get SQLAlchemy database URL"""
        return cls.DATABASE_URL

    @classmethod
    def get_season_path(cls, season: int):
        """Get path to season data directory"""
        return cls.DATA_PATH / f'season-{season}'

    @classmethod
    def get_matches_path(cls, season: int):
        """Get path to season matches directory"""
        return cls.get_season_path(season) / 'matches'


# Create singleton instance
config = Config()
