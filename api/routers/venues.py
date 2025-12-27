"""
Venues API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from api.models.schemas import (
    VenueBase,
    VenueDetail,
    VenueList,
    VenueMachineStats,
    VenueWithStats,
    VenueWithStatsList,
    VenueHomeTeam,
    ErrorResponse
)
from api.dependencies import execute_query

router = APIRouter(prefix="/venues", tags=["venues"])


def get_current_machines_for_venue(venue_key: str) -> List[str]:
    """
    Get the current machine lineup for a venue from the database.
    Returns list of machine keys from the most recent season where this venue has data.
    """
    try:
        # Get machines from the most recent season for this venue
        query = """
            SELECT vm.machine_key
            FROM venue_machines vm
            WHERE vm.venue_key = :venue_key
            AND vm.season = (
                SELECT MAX(season) FROM venue_machines WHERE venue_key = :venue_key
            )
            AND vm.active = true
            ORDER BY vm.machine_key
        """
        results = execute_query(query, {'venue_key': venue_key})
        return [row['machine_key'] for row in results]
    except Exception:
        return []


@router.get(
    "",
    response_model=VenueList,
    summary="List all venues",
    description="Get a paginated list of all venues with optional filtering"
)
def list_venues(
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    search: Optional[str] = Query(None, description="Search venue names (case-insensitive)"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all venues with optional filtering and pagination.

    Example queries:
    - `/venues` - All venues
    - `/venues?neighborhood=Ballard` - All Ballard venues
    - `/venues?search=Tavern` - Search for "Tavern" venues
    """
    # Build WHERE clauses
    where_clauses = []
    params = {}

    if neighborhood:
        where_clauses.append("LOWER(v.neighborhood) = LOWER(:neighborhood)")
        params['neighborhood'] = neighborhood

    if search:
        where_clauses.append("LOWER(v.venue_name) LIKE LOWER(:search)")
        params['search'] = f"%{search}%"

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM venues v WHERE {where_clause}"
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated results
    query = f"""
        SELECT venue_key, venue_name, address, neighborhood
        FROM venues v
        WHERE {where_clause}
        ORDER BY venue_name
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    venues = execute_query(query, params)

    return VenueList(
        venues=[VenueBase(**venue) for venue in venues],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/with-stats",
    response_model=VenueWithStatsList,
    summary="List all venues with statistics",
    description="Get a paginated list of all venues with machine count and home teams"
)
def list_venues_with_stats(
    season: Optional[int] = Query(None, description="Filter home teams by season (defaults to most recent)"),
    neighborhood: Optional[str] = Query(None, description="Filter by neighborhood"),
    search: Optional[str] = Query(None, description="Search venue names (case-insensitive)"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all venues with additional statistics including machine count and home teams.

    Example queries:
    - `/venues/with-stats` - All venues with stats
    - `/venues/with-stats?season=22` - Home teams filtered to season 22
    - `/venues/with-stats?search=Tavern` - Search for "Tavern" venues
    """
    # Build WHERE clauses
    where_clauses = []
    params = {}

    if neighborhood:
        where_clauses.append("LOWER(v.neighborhood) = LOWER(:neighborhood)")
        params['neighborhood'] = neighborhood

    if search:
        where_clauses.append("LOWER(v.venue_name) LIKE LOWER(:search)")
        params['search'] = f"%{search}%"

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM venues v WHERE {where_clause}"
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Get paginated venues
    query = f"""
        SELECT venue_key, venue_name, address, neighborhood
        FROM venues v
        WHERE {where_clause}
        ORDER BY venue_name
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    venues = execute_query(query, params)

    # Get home teams for each venue
    # If season not specified, get most recent season
    if season is None:
        season_query = "SELECT MAX(season) as max_season FROM teams"
        season_result = execute_query(season_query, {})
        season = season_result[0]['max_season'] if season_result and season_result[0]['max_season'] else 22

    home_teams_query = """
        SELECT team_key, team_name, home_venue_key, season
        FROM teams
        WHERE season = :season
    """
    home_teams_result = execute_query(home_teams_query, {'season': season})

    # Group home teams by venue
    venue_home_teams = {}
    for team in home_teams_result:
        venue_key = team['home_venue_key']
        if venue_key:
            if venue_key not in venue_home_teams:
                venue_home_teams[venue_key] = []
            venue_home_teams[venue_key].append(VenueHomeTeam(
                team_key=team['team_key'],
                team_name=team['team_name'],
                season=team['season']
            ))

    # Build enriched venue list
    enriched_venues = []
    for venue in venues:
        venue_key = venue['venue_key']

        # Get current machine count for this venue
        current_machines = get_current_machines_for_venue(venue_key)
        machine_count = len(current_machines)

        # Get home teams for this venue
        home_teams = venue_home_teams.get(venue_key, [])

        enriched_venues.append(VenueWithStats(
            venue_key=venue_key,
            venue_name=venue['venue_name'],
            address=venue.get('address'),
            neighborhood=venue.get('neighborhood'),
            machine_count=machine_count,
            home_teams=home_teams
        ))

    return VenueWithStatsList(
        venues=enriched_venues,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{venue_key}",
    response_model=VenueDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get venue details",
    description="Get detailed information about a specific venue"
)
def get_venue(venue_key: str):
    """
    Get detailed information about a specific venue by its venue_key.

    Example: `/venues/T4B`
    """
    query = """
        SELECT
            v.venue_key,
            v.venue_name,
            v.address,
            v.neighborhood
        FROM venues v
        WHERE v.venue_key = :venue_key
    """
    venues = execute_query(query, {'venue_key': venue_key})

    if not venues:
        raise HTTPException(status_code=404, detail=f"Venue '{venue_key}' not found")

    # Get home teams for this venue (from most recent season)
    season_query = "SELECT MAX(season) as max_season FROM teams"
    season_result = execute_query(season_query, {})
    season = season_result[0]['max_season'] if season_result and season_result[0]['max_season'] else 22

    home_teams_query = """
        SELECT team_key, team_name, season
        FROM teams
        WHERE home_venue_key = :venue_key AND season = :season
    """
    home_teams_result = execute_query(home_teams_query, {'venue_key': venue_key, 'season': season})
    home_teams = [VenueHomeTeam(**team) for team in home_teams_result]

    return VenueDetail(**venues[0], home_teams=home_teams)


@router.get(
    "/{venue_key}/machines",
    response_model=List[VenueMachineStats],
    responses={404: {"model": ErrorResponse}},
    summary="Get machines at a venue with score statistics",
    description="Get all machines that have been played at this venue with score statistics"
)
def get_venue_machines(
    venue_key: str,
    current_only: bool = Query(False, description="Filter to only show current machines at this venue"),
    seasons: Optional[List[int]] = Query(None, description="Filter by one or more seasons"),
    team_key: Optional[str] = Query(None, description="Filter statistics to a specific team"),
    scores_from: str = Query("venue", description="Score source: 'venue' (only scores at this venue) or 'all' (all scores on these machines across all venues)")
):
    """
    Get all machines that have been played at this venue with statistics.

    Parameters:
    - current_only: If true, only returns machines currently at the venue (based on most recent match)
    - seasons: Filter scores to one or more seasons (e.g., seasons=21&seasons=22)
    - team_key: Filter statistics to show only this team's performance
    - scores_from: 'venue' = only scores at this venue, 'all' = all scores on these machines (useful for team experience)

    Example queries:
    - `/venues/T4B/machines` - All machines ever played at 4Bs Tavern
    - `/venues/T4B/machines?current_only=true` - Only current machines at 4Bs Tavern
    - `/venues/T4B/machines?current_only=true&team_key=SKP&scores_from=all` - Current machines at 4Bs, showing SKP's experience across all venues
    - `/venues/T4B/machines?seasons=22` - Machines played at 4Bs in season 22
    - `/venues/T4B/machines?seasons=21&seasons=22` - Machines played at 4Bs in seasons 21 and 22
    """
    # First verify venue exists
    venue_query = "SELECT venue_name FROM venues WHERE venue_key = :venue_key"
    venue_result = execute_query(venue_query, {'venue_key': venue_key})
    if not venue_result:
        raise HTTPException(status_code=404, detail=f"Venue '{venue_key}' not found")

    venue_name = venue_result[0]['venue_name']

    # Get current machines list (always get it for is_current flag)
    current_machines = get_current_machines_for_venue(venue_key)

    # If filtering by current only and no current machines found, return empty list
    if current_only and not current_machines:
        return []

    # Build WHERE clauses based on scores_from parameter
    where_clauses = []
    params = {}

    # Determine which machines to include
    machines_to_include = current_machines if current_only and current_machines else None

    if machines_to_include:
        # Filter to specific machines
        placeholders = ','.join([f":machine_{i}" for i in range(len(machines_to_include))])
        where_clauses.append(f"s.machine_key IN ({placeholders})")
        for i, machine_key in enumerate(machines_to_include):
            params[f'machine_{i}'] = machine_key
    elif scores_from == "venue":
        # If not filtering by current machines, still limit to machines played at this venue
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    # Handle scores_from parameter
    if scores_from == "venue" and not machines_to_include:
        # Already added venue filter above
        pass
    elif scores_from == "venue" and machines_to_include:
        # For current machines, also filter to only scores at this venue
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key
    # else scores_from == "all": no venue filter, get all scores on these machines

    if seasons is not None and len(seasons) > 0:
        where_clauses.append("s.season = ANY(:seasons)")
        params['seasons'] = seasons

    if team_key is not None:
        where_clauses.append("s.team_key = :team_key")
        params['team_key'] = team_key

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get machine statistics
    query = f"""
        SELECT
            m.machine_key,
            m.machine_name,
            m.manufacturer,
            m.year,
            COUNT(s.score_id) as total_scores,
            COUNT(DISTINCT s.player_key) as unique_players,
            COALESCE(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.score) AS INTEGER), 0) as median_score,
            COALESCE(MAX(s.score), 0) as max_score,
            COALESCE(MIN(s.score), 0) as min_score,
            COALESCE(CAST(AVG(s.score) AS INTEGER), 0) as avg_score
        FROM machines m
        INNER JOIN scores s ON m.machine_key = s.machine_key
        WHERE {where_clause}
        GROUP BY m.machine_key, m.machine_name, m.manufacturer, m.year
        ORDER BY m.machine_name
    """

    machines = execute_query(query, params)

    # Add venue information, is_current flag, and ensure venue_key is set
    for machine in machines:
        if 'venue_key' not in machine or not machine['venue_key']:
            machine['venue_key'] = venue_key
        if 'venue_name' not in machine or not machine['venue_name']:
            machine['venue_name'] = venue_name
        # Set is_current flag based on whether machine is in current_machines list
        machine['is_current'] = machine['machine_key'] in current_machines if current_machines else False

    return [VenueMachineStats(**machine) for machine in machines]


@router.get(
    "/{venue_key}/current-machines",
    response_model=List[str],
    responses={404: {"model": ErrorResponse}},
    summary="Get current machine lineup at venue",
    description="Get list of machine keys currently at this venue (from most recent match)"
)
def get_venue_current_machines(venue_key: str):
    """
    Get the current machine lineup at a venue based on the most recent match data.

    Returns a list of machine keys (e.g., ["MM", "TZ", "AFM", ...])

    Example: `/venues/T4B/current-machines`
    """
    # First verify venue exists
    venue_query = "SELECT venue_name FROM venues WHERE venue_key = :venue_key"
    venue_result = execute_query(venue_query, {'venue_key': venue_key})
    if not venue_result:
        raise HTTPException(status_code=404, detail=f"Venue '{venue_key}' not found")

    current_machines = get_current_machines_for_venue(venue_key)

    if not current_machines:
        raise HTTPException(
            status_code=404,
            detail=f"No recent match data found for venue '{venue_key}'"
        )

    return current_machines
