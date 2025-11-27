"""
Machines API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from api.models.schemas import (
    MachineBase,
    MachineDetail,
    MachineList,
    MachinePercentiles,
    ScorePercentile,
    MachineScore,
    MachineScoreList,
    ErrorResponse
)
from api.dependencies import execute_query
from etl.database import db

router = APIRouter(prefix="/machines", tags=["machines"])


@router.get(
    "",
    response_model=MachineList,
    summary="List all machines",
    description="Get a paginated list of all machines with optional filtering"
)
def list_machines(
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    year: Optional[int] = Query(None, description="Filter by year"),
    game_type: Optional[str] = Query(None, description="Filter by game type (SS, EM, etc.)"),
    search: Optional[str] = Query(None, description="Search machine names (case-insensitive)"),
    has_percentiles: Optional[bool] = Query(None, description="Filter machines with percentile data"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all machines with optional filtering and pagination.

    Example queries:
    - `/machines` - All machines
    - `/machines?manufacturer=Stern` - All Stern machines
    - `/machines?year=2022` - Machines from 2022
    - `/machines?search=Star Wars` - Search for "Star Wars" machines
    - `/machines?has_percentiles=true` - Only machines with score percentile data
    """
    # Build WHERE clauses
    where_clauses = []
    params = {}

    if manufacturer:
        where_clauses.append("LOWER(m.manufacturer) = LOWER(:manufacturer)")
        params['manufacturer'] = manufacturer

    if year is not None:
        where_clauses.append("m.year = :year")
        params['year'] = year

    if game_type:
        where_clauses.append("LOWER(m.game_type) = LOWER(:game_type)")
        params['game_type'] = game_type

    if search:
        where_clauses.append("(LOWER(m.machine_name) LIKE LOWER(:search) OR LOWER(m.machine_key) LIKE LOWER(:search))")
        params['search'] = f"%{search}%"

    if has_percentiles is not None:
        if has_percentiles:
            where_clauses.append("EXISTS (SELECT 1 FROM score_percentiles sp WHERE sp.machine_key = m.machine_key)")
        else:
            where_clauses.append("NOT EXISTS (SELECT 1 FROM score_percentiles sp WHERE sp.machine_key = m.machine_key)")

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM machines m WHERE {where_clause}"
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated results
    query = f"""
        SELECT machine_key, machine_name, manufacturer, year, game_type
        FROM machines m
        WHERE {where_clause}
        ORDER BY machine_name
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    machines = execute_query(query, params)

    return MachineList(
        machines=[MachineBase(**machine) for machine in machines],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{machine_key}",
    response_model=MachineDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get machine details",
    description="Get detailed information about a specific machine"
)
def get_machine(machine_key: str):
    """
    Get detailed information about a specific machine by its machine_key.

    Example: `/machines/SternWars`
    """
    query = """
        SELECT
            m.machine_key,
            m.machine_name,
            m.manufacturer,
            m.year,
            m.game_type,
            COALESCE(COUNT(s.score_id), 0) as total_scores,
            COALESCE(COUNT(DISTINCT s.player_key), 0) as unique_players,
            COALESCE(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.score) AS INTEGER), 0) as median_score,
            COALESCE(MAX(s.score), 0) as max_score
        FROM machines m
        LEFT JOIN scores s ON m.machine_key = s.machine_key
        WHERE m.machine_key = :machine_key
        GROUP BY m.machine_key, m.machine_name, m.manufacturer, m.year, m.game_type
    """
    machines = execute_query(query, {'machine_key': machine_key})

    if not machines:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    return MachineDetail(**machines[0])


@router.get(
    "/{machine_key}/percentiles",
    response_model=List[MachinePercentiles],
    responses={404: {"model": ErrorResponse}},
    summary="Get machine score percentiles",
    description="Get score percentile data for a specific machine"
)
def get_machine_percentiles(
    machine_key: str,
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue (use '_ALL_' for aggregate stats)")
):
    """
    Get score percentile data for a specific machine.

    Returns percentiles (10th, 25th, 50th, 75th, 90th, 95th, 99th) for the machine.

    Example queries:
    - `/machines/SternWars/percentiles` - All percentile data for Star Wars
    - `/machines/SternWars/percentiles?season=22` - Season 22 only
    - `/machines/SternWars/percentiles?venue_key=_ALL_` - Aggregate across all venues
    - `/machines/SternWars/percentiles?venue_key=JUP` - Jupiter venue only
    """
    # First verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {'machine_key': machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    machine_name = machine_result[0]['machine_name']

    # Build WHERE clauses
    where_clauses = ["sp.machine_key = :machine_key"]
    params = {'machine_key': machine_key}

    if season is not None:
        where_clauses.append("sp.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("sp.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Get percentile data grouped by venue/season
    query = f"""
        SELECT
            sp.machine_key,
            sp.venue_key,
            sp.season,
            sp.sample_size,
            sp.percentile,
            sp.score_threshold
        FROM score_percentiles sp
        WHERE {where_clause}
        ORDER BY sp.season, sp.venue_key, sp.percentile
    """
    rows = execute_query(query, params)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No percentile data found for machine '{machine_key}'"
        )

    # Group by venue_key and season
    grouped = {}
    for row in rows:
        key = (row['venue_key'], row['season'])
        if key not in grouped:
            grouped[key] = {
                'machine_key': machine_key,
                'machine_name': machine_name,
                'venue_key': row['venue_key'],
                'season': row['season'],
                'sample_size': row['sample_size'],
                'percentiles': {}
            }
        grouped[key]['percentiles'][row['percentile']] = row['score_threshold']

    return [MachinePercentiles(**data) for data in grouped.values()]


@router.get(
    "/{machine_key}/percentiles/raw",
    response_model=List[ScorePercentile],
    responses={404: {"model": ErrorResponse}},
    summary="Get raw machine score percentiles",
    description="Get raw score percentile records for a specific machine (one record per percentile)"
)
def get_machine_percentiles_raw(
    machine_key: str,
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    percentile: Optional[int] = Query(None, ge=0, le=100, description="Filter by specific percentile")
):
    """
    Get raw score percentile records for a specific machine.

    Returns individual records for each percentile/venue/season combination.

    Example queries:
    - `/machines/SternWars/percentiles/raw` - All raw percentile records
    - `/machines/SternWars/percentiles/raw?percentile=50` - Just median scores
    - `/machines/SternWars/percentiles/raw?season=22&venue_key=_ALL_` - Season 22 aggregate
    """
    # First verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {'machine_key': machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    machine_name = machine_result[0]['machine_name']

    # Build WHERE clauses
    where_clauses = ["sp.machine_key = :machine_key"]
    params = {'machine_key': machine_key}

    if season is not None:
        where_clauses.append("sp.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("sp.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if percentile is not None:
        where_clauses.append("sp.percentile = :percentile")
        params['percentile'] = percentile

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
            sp.machine_key,
            sp.venue_key,
            sp.percentile,
            sp.score_threshold,
            sp.sample_size,
            sp.season
        FROM score_percentiles sp
        WHERE {where_clause}
        ORDER BY sp.season, sp.venue_key, sp.percentile
    """
    rows = execute_query(query, params)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No percentile data found for machine '{machine_key}'"
        )

    # Add machine_name to each row
    for row in rows:
        row['machine_name'] = machine_name

    return [ScorePercentile(**row) for row in rows]


@router.get(
    "/{machine_key}/scores",
    response_model=MachineScoreList,
    responses={404: {"model": ErrorResponse}},
    summary="Get all scores for a machine",
    description="Get individual score records for a specific machine with optional filtering"
)
def get_machine_scores(
    machine_key: str,
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    team_keys: Optional[str] = Query(None, description="Filter by team keys (comma-separated, e.g., 'SKP,TRL,ADB')"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get all individual scores for a specific machine with optional filtering.

    Example queries:
    - `/machines/MM/scores` - All scores for Medieval Madness
    - `/machines/MM/scores?season=22` - Season 22 scores only
    - `/machines/MM/scores?venue_key=T4B` - Scores from 4Bs Tavern only
    - `/machines/MM/scores?team_keys=SKP,TRL` - Scores from Slap Kraken Pop and Trolls teams
    - `/machines/MM/scores?season=22&venue_key=T4B` - Season 22 scores from 4Bs Tavern
    """
    # First verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {'machine_key': machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    # Build WHERE clauses
    where_clauses = ["s.machine_key = :machine_key"]
    params = {'machine_key': machine_key}

    if season is not None:
        where_clauses.append("s.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if team_keys is not None:
        # Parse comma-separated team keys
        team_list = [tk.strip() for tk in team_keys.split(',') if tk.strip()]
        if team_list:
            placeholders = ','.join([f":team_{i}" for i in range(len(team_list))])
            where_clauses.append(f"s.team_key IN ({placeholders})")
            for i, team_key in enumerate(team_list):
                params[f'team_{i}'] = team_key

    where_clause = " AND ".join(where_clauses)

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM scores s WHERE {where_clause}"
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated scores with player and venue names
    query = f"""
        SELECT
            s.score_id,
            s.score,
            s.player_key,
            p.name as player_name,
            s.venue_key,
            v.venue_name,
            s.season,
            s.week,
            s.round_number,
            s.match_key,
            s.date,
            s.player_position,
            s.team_key
        FROM scores s
        LEFT JOIN players p ON s.player_key = p.player_key
        LEFT JOIN venues v ON s.venue_key = v.venue_key
        WHERE {where_clause}
        ORDER BY s.score DESC
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    scores = execute_query(query, params)

    return MachineScoreList(
        scores=[MachineScore(**score) for score in scores],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{machine_key}/venues",
    response_model=List[dict],
    responses={404: {"model": ErrorResponse}},
    summary="Get venues where machine has been played",
    description="Get list of venues with score counts for a specific machine"
)
def get_machine_venues(machine_key: str):
    """
    Get list of venues where this machine has been played, with score counts.

    Returns venue_key, venue_name, and score count for each venue.
    """
    # First verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {'machine_key': machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    query = """
        SELECT
            v.venue_key,
            v.venue_name,
            COUNT(s.score_id) as score_count
        FROM venues v
        INNER JOIN scores s ON v.venue_key = s.venue_key
        WHERE s.machine_key = :machine_key
        GROUP BY v.venue_key, v.venue_name
        ORDER BY v.venue_name
    """
    venues = execute_query(query, {'machine_key': machine_key})

    return venues


@router.get(
    "/{machine_key}/teams",
    response_model=List[dict],
    responses={404: {"model": ErrorResponse}},
    summary="Get teams that have played on a machine",
    description="Get list of teams with score counts for a specific machine"
)
def get_machine_teams(machine_key: str):
    """
    Get list of teams that have played on this machine, with score counts.

    Returns team_key, team_name, and score count for each team.
    """
    # First verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {'machine_key': machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    query = """
        SELECT
            t.team_key,
            t.team_name,
            COUNT(s.score_id) as score_count
        FROM teams t
        INNER JOIN scores s ON t.team_key = s.team_key AND t.season = s.season
        WHERE s.machine_key = :machine_key
        GROUP BY t.team_key, t.team_name
        ORDER BY t.team_name
    """
    teams = execute_query(query, {'machine_key': machine_key})

    return teams
