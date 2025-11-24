"""
MNP Analyzer API

FastAPI application for Minnesota Pinball League data analysis.
Provides REST endpoints for accessing player stats, machine data, and score percentiles.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.routers import players, machines

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MNP Analyzer API",
    description="""
    Minnesota Pinball League (MNP) Data Analysis API

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

    Data is sourced from the Minnesota Pinball League (MNP) match archives.
    Currently includes Season 22 data with 523 players, 341 machines, and 10,680+ scores.

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(players.router)
app.include_router(machines.router)


@app.get("/", tags=["root"])
def read_root():
    """
    API root endpoint - provides basic information and available endpoints
    """
    return {
        "message": "Welcome to MNP Analyzer API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "endpoints": {
            "players": "/players",
            "machines": "/machines"
        },
        "data_summary": {
            "description": "Minnesota Pinball League Season 22 data",
            "players": 523,
            "machines": 341,
            "venues": 19,
            "teams": 34,
            "matches": 184,
            "total_scores": "10,680+"
        }
    }


@app.get("/health", tags=["root"])
def health_check():
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
