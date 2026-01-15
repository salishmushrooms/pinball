"""
MNP Analyzer API

FastAPI application for Monday Night Pinball data analysis.
Provides REST endpoints for accessing player stats, machine data, and score percentiles.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routers import players, machines, venues, teams, matchups, seasons, predictions, matchplay
from etl.database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    Initialize database with connection pooling on startup.
    """
    # Startup: Connect to database with pooling enabled for API performance
    logger.info("Initializing database connection with pooling...")
    db.connect(use_pool=True)
    logger.info("Database connection pool initialized")

    yield

    # Shutdown: Close database connections
    logger.info("Closing database connections...")
    db.close()
    logger.info("Database connections closed")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Caching middleware
class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Add Cache-Control headers to API responses.
    Data changes once per week, so we can cache aggressively.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only add caching headers for GET requests
        if request.method == "GET":
            # Cache for 1 week (604800 seconds)
            # Use stale-while-revalidate to serve stale content while fetching fresh data
            response.headers["Cache-Control"] = "public, max-age=604800, stale-while-revalidate=86400"
            # Add ETag support hint
            response.headers["Vary"] = "Accept-Encoding"

        return response


# Create FastAPI app with lifespan for connection pooling
app = FastAPI(
    title="MNP Analyzer API",
    lifespan=lifespan,
    description="""
    Monday Night Pinball (MNP) Data Analysis API

    This API provides access to:
    - Player statistics and performance data
    - Machine information and score percentiles
    - Match history and game results

    ## Features

    - **Player Endpoints**: Search players, view detailed stats, and analyze performance by machine
    - **Machine Endpoints**: Browse machines, view score percentiles for difficulty analysis
    - **Filtering & Pagination**: All list endpoints support filtering and pagination
    - **Score Percentiles**: Understand score distributions to normalize performance across different machines

    ## Data Source

    Data is sourced from the Monday Night Pinball (MNP) match archives.
    Currently includes Seasons 18-23 with 936+ players, 400+ machines, and 56,000+ scores across 943+ matches.

    ## Tips

    - Use `venue_key='_ALL_'` to get aggregate statistics across all venues
    - Score percentiles help normalize player performance across different machines
    - Player machine stats show average percentile (0-100) for standardized comparison
    """,
    version="1.0.0",
    contact={
        "name": "MNP Analyzer",
        "url": "https://github.com/yourusername/mnp-analyzer"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add caching middleware
app.add_middleware(CacheControlMiddleware)

# Include routers
app.include_router(players.router)
app.include_router(machines.router)
app.include_router(venues.router)
app.include_router(teams.router)
app.include_router(matchups.router)
app.include_router(seasons.router)
app.include_router(predictions.router)
app.include_router(matchplay.router)


@app.get("/", tags=["root"])
@limiter.limit("120/minute")  # Lightweight endpoint - higher limit
def read_root(request: Request):
    """
    API root endpoint - provides basic information and available endpoints
    """
    from etl.database import db
    from sqlalchemy import text

    # Query actual database statistics
    data_summary = {
        "description": "Monday Night Pinball Seasons 20-23 data",
        "players": 0,
        "machines": 0,
        "venues": 0,
        "teams": 0,
        "matches": 0,
        "total_scores": "0"
    }

    try:
        if not db.engine:
            db.connect()
        with db.engine.connect() as conn:
            # Get total unique players
            result = conn.execute(text("SELECT COUNT(*) FROM players"))
            data_summary["players"] = result.scalar()

            # Get total machines
            result = conn.execute(text("SELECT COUNT(*) FROM machines"))
            data_summary["machines"] = result.scalar()

            # Get total venues
            result = conn.execute(text("SELECT COUNT(*) FROM venues"))
            data_summary["venues"] = result.scalar()

            # Get total teams (counting distinct team_key across all seasons)
            result = conn.execute(text("SELECT COUNT(DISTINCT team_key) FROM teams"))
            data_summary["teams"] = result.scalar()

            # Get total matches
            result = conn.execute(text("SELECT COUNT(*) FROM matches"))
            data_summary["matches"] = result.scalar()

            # Get total scores
            result = conn.execute(text("SELECT COUNT(*) FROM scores"))
            total_scores = result.scalar()
            data_summary["total_scores"] = f"{total_scores:,}" if total_scores else "0"

    except Exception as e:
        logger.error(f"Failed to fetch data summary: {e}")
        # Return default values if database query fails

    return {
        "message": "Welcome to MNP Analyzer API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "players": "/players",
            "machines": "/machines",
            "venues": "/venues",
            "teams": "/teams",
            "matchups": "/matchups",
            "matchplay": "/matchplay"
        },
        "data_summary": data_summary
    }


@app.get("/seasons", tags=["root"])
@limiter.limit("120/minute")  # Lightweight endpoint
def get_seasons(request: Request):
    """
    Get all available seasons in the database

    Returns a list of season numbers sorted in ascending order.
    """
    from etl.database import db
    from sqlalchemy import text

    try:
        if not db.engine:
            db.connect()
        with db.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT DISTINCT season FROM matches ORDER BY season ASC"
            ))
            seasons = [row[0] for row in result]

        return {
            "seasons": seasons,
            "count": len(seasons)
        }
    except Exception as e:
        logger.error(f"Failed to fetch seasons: {e}")
        return {
            "seasons": [20, 21, 22, 23],  # Fallback to known seasons
            "count": 4
        }


@app.get("/health", tags=["root"])
@limiter.limit("300/minute")  # Health checks - very high limit
def health_check(request: Request):
    """
    Health check endpoint for monitoring
    """
    from etl.database import db
    from sqlalchemy import text

    try:
        if not db.engine:
            db.connect()
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "api_version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch unexpected errors
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
