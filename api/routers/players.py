"""
Players API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from api.models.schemas import (
    PlayerBase,
    PlayerDetail,
    PlayerList,
    PlayerMachineStats,
    PlayerMachineStatsList,
    ErrorResponse
)
from api.dependencies import execute_query
from etl.database import db

router = APIRouter(prefix="/players", tags=["players"])


@router.get(
    "",
    response_model=PlayerList,
    summary="List all players",
    description="Get a paginated list of all players with optional filtering"
)
def list_players(
    season: Optional[int] = Query(None, description="Filter by season (players active in this season)"),
    min_ipr: Optional[float] = Query(None, description="Minimum IPR rating"),
    max_ipr: Optional[float] = Query(None, description="Maximum IPR rating"),
    search: Optional[str] = Query(None, description="Search player names (case-insensitive)"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all players with optional filtering and pagination.

    Example queries:
    - `/players` - All players
    - `/players?season=22` - Players active in season 22
    - `/players?min_ipr=1500` - Players with IPR >= 1500
    - `/players?search=John` - Players with "John" in their name
    """
    # Build WHERE clauses
    where_clauses = []
    params = {}

    if season is not None:
        where_clauses.append("(first_seen_season <= :season AND last_seen_season >= :season)")
        params['season'] = season

    if min_ipr is not None:
        where_clauses.append("current_ipr >= :min_ipr")
        params['min_ipr'] = min_ipr

    if max_ipr is not None:
        where_clauses.append("current_ipr <= :max_ipr")
        params['max_ipr'] = max_ipr

    if search:
        where_clauses.append("LOWER(name) LIKE LOWER(:search)")
        params['search'] = f"%{search}%"

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM players WHERE {where_clause}"
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated results
    query = f"""
        SELECT player_key, name, current_ipr, first_seen_season, last_seen_season
        FROM players
        WHERE {where_clause}
        ORDER BY name
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    players = execute_query(query, params)

    return PlayerList(
        players=[PlayerBase(**player) for player in players],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{player_key}",
    response_model=PlayerDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get player details",
    description="Get detailed information about a specific player"
)
def get_player(player_key: str):
    """
    Get detailed information about a specific player by their player_key.

    Example: `/players/sean_irby`
    """
    query = """
        SELECT player_key, name, current_ipr, first_seen_season, last_seen_season,
               created_at, updated_at
        FROM players
        WHERE player_key = :player_key
    """
    players = execute_query(query, {'player_key': player_key})

    if not players:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    return PlayerDetail(**players[0])


@router.get(
    "/{player_key}/machines",
    response_model=PlayerMachineStatsList,
    responses={404: {"model": ErrorResponse}},
    summary="Get player machine statistics",
    description="Get performance statistics for a player across all machines they've played"
)
def get_player_machine_stats(
    player_key: str,
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue (use '_ALL_' for aggregate stats)"),
    min_games: int = Query(1, ge=1, description="Minimum games played on machine"),
    sort_by: str = Query("median_percentile", description="Sort field: median_percentile, avg_percentile, games_played, avg_score, best_score"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get performance statistics for a player across different machines.

    Example queries:
    - `/players/sean_irby/machines` - All machines Sean has played
    - `/players/sean_irby/machines?season=22` - Season 22 only
    - `/players/sean_irby/machines?venue_key=_ALL_` - Aggregate stats across all venues
    - `/players/sean_irby/machines?min_games=5` - Only machines with 5+ games played
    - `/players/sean_irby/machines?sort_by=games_played&sort_order=desc` - Sort by games played
    """
    # Validate sort parameters
    valid_sort_fields = ["median_percentile", "avg_percentile", "games_played", "avg_score", "best_score"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of: {valid_sort_fields}")

    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")

    # First verify player exists
    player_check = execute_query("SELECT 1 FROM players WHERE player_key = :player_key", {'player_key': player_key})
    if not player_check:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    # Build WHERE clauses
    where_clauses = ["pms.player_key = :player_key", "pms.games_played >= :min_games"]
    params = {'player_key': player_key, 'min_games': min_games}

    if season is not None:
        where_clauses.append("pms.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("pms.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM player_machine_stats pms
        WHERE {where_clause}
    """
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated results with machine and player names
    query = f"""
        SELECT
            pms.player_key,
            p.name as player_name,
            pms.machine_key,
            m.machine_name,
            pms.venue_key,
            pms.season,
            pms.games_played,
            pms.total_score,
            pms.median_score,
            pms.avg_score,
            pms.best_score,
            pms.worst_score,
            pms.median_percentile,
            pms.avg_percentile
        FROM player_machine_stats pms
        JOIN players p ON pms.player_key = p.player_key
        JOIN machines m ON pms.machine_key = m.machine_key
        WHERE {where_clause}
        ORDER BY pms.{sort_by} {sort_order.upper()}
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    stats = execute_query(query, params)

    return PlayerMachineStatsList(
        stats=[PlayerMachineStats(**stat) for stat in stats],
        total=total,
        limit=limit,
        offset=offset
    )
