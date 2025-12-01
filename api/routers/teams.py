"""
Teams API endpoints
"""
from typing import Optional, List, Dict, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from collections import defaultdict
import numpy as np

from api.models.schemas import (
    TeamBase,
    TeamList,
    TeamDetail,
    TeamMachineStats,
    TeamMachineStatsList,
    TeamPlayer,
    TeamPlayerList,
    ErrorResponse
)
from api.dependencies import execute_query
from etl.database import db

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "",
    response_model=TeamList,
    summary="List all teams",
    description="Get a list of all teams with optional filtering"
)
def list_teams(
    season: Optional[int] = Query(None, description="Filter by season"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    List all teams with optional filtering and pagination.

    Example queries:
    - `/teams` - All teams
    - `/teams?season=22` - All teams from season 22
    """
    # Build WHERE clauses
    where_clauses = []
    params = {}

    if season is not None:
        where_clauses.append("t.season = :season")
        params['season'] = season

    where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"

    # Get paginated results - get all teams
    query = f"""
        SELECT
            t.team_key,
            t.team_name,
            t.home_venue_key,
            t.season
        FROM teams t
        WHERE {where_clause}
        ORDER BY t.team_name, t.season DESC
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = limit
    params['offset'] = offset
    teams = execute_query(query, params)

    # Get total count based on actual results
    total = len(teams)

    return TeamList(
        teams=[TeamBase(**team) for team in teams],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{team_key}",
    response_model=TeamDetail,
    responses={404: {"model": ErrorResponse}},
    summary="Get team details",
    description="Get detailed information about a specific team"
)
def get_team(
    team_key: str,
    season: Optional[int] = Query(None, description="Filter by season")
):
    """
    Get detailed information about a specific team.

    Example: `/teams/SKP?season=22`
    """
    # Build WHERE clause
    where_clauses = ["t.team_key = :team_key"]
    params = {'team_key': team_key}

    if season is not None:
        where_clauses.append("t.season = :season")
        params['season'] = season

    where_clause = " AND ".join(where_clauses)

    query = f"""
        SELECT
            t.team_key,
            t.team_name,
            t.home_venue_key,
            t.season
        FROM teams t
        WHERE {where_clause}
        ORDER BY t.season DESC
        LIMIT 1
    """
    teams = execute_query(query, params)

    if not teams:
        raise HTTPException(status_code=404, detail=f"Team '{team_key}' not found")

    return TeamDetail(**teams[0])


def calculate_team_win_percentage(
    team_key: str,
    seasons: Optional[List[int]] = None,
    venue_key: Optional[str] = None,
    rounds: Optional[List[int]] = None,
    exclude_subs: bool = True
) -> Dict[str, float]:
    """
    Calculate win percentage for a team on each machine using optimized batch query.

    Win percentage is calculated by comparing team player scores to opponent scores.

    Args:
        team_key: Team's unique key
        seasons: Optional list of seasons to filter
        venue_key: Optional venue filter
        rounds: Optional list of rounds to filter (1-4)
        exclude_subs: Exclude substitute players (default: true)

    Returns:
        Dict mapping machine_key to win percentage (0-100)
    """
    # Build WHERE clause for filtering
    where_clauses = ["team_scores.team_key = :team_key"]
    params = {'team_key': team_key}

    if seasons is not None and len(seasons) > 0:
        season_placeholders = ', '.join([f':season_{i}' for i in range(len(seasons))])
        where_clauses.append(f"team_scores.season IN ({season_placeholders})")
        for i, season in enumerate(seasons):
            params[f'season_{i}'] = season

    if venue_key is not None:
        where_clauses.append("team_scores.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if rounds is not None and len(rounds) > 0:
        placeholders = ', '.join([f':round_{i}' for i in range(len(rounds))])
        where_clauses.append(f"team_scores.round_number IN ({placeholders})")
        for i, r in enumerate(rounds):
            params[f'round_{i}'] = r

    if exclude_subs:
        where_clauses.append("(team_scores.is_substitute IS NULL OR team_scores.is_substitute = false)")
        where_clauses.append("(opp_scores.is_substitute IS NULL OR opp_scores.is_substitute = false)")

    where_clause = " AND ".join(where_clauses)

    # Optimized batch query using self-join to compare team vs opponent scores
    query = f"""
        SELECT
            team_scores.machine_key,
            COUNT(*) as total_comparisons,
            SUM(CASE WHEN team_scores.score > opp_scores.score THEN 1 ELSE 0 END) as wins
        FROM scores team_scores
        INNER JOIN scores opp_scores
            ON team_scores.match_key = opp_scores.match_key
            AND team_scores.round_number = opp_scores.round_number
            AND team_scores.machine_key = opp_scores.machine_key
            AND team_scores.team_key != opp_scores.team_key
        WHERE {where_clause}
        GROUP BY team_scores.machine_key
    """

    results = execute_query(query, params)

    # Calculate win percentages
    win_percentages = {}
    for row in results:
        machine_key = row['machine_key']
        total = row['total_comparisons']
        wins = row['wins']

        if total > 0:
            win_percentages[machine_key] = (wins / total) * 100.0
        else:
            win_percentages[machine_key] = None

    return win_percentages


@router.get(
    "/{team_key}/machines",
    response_model=TeamMachineStatsList,
    responses={404: {"model": ErrorResponse}},
    summary="Get team machine statistics",
    description="Get performance statistics for a team across all machines they've played"
)
def get_team_machine_stats(
    team_key: str,
    seasons: Union[List[int], None] = Query(None, description="Filter by season(s) - can pass multiple"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    rounds: Optional[str] = Query(None, description="Filter by rounds (comma-separated, e.g., '1,2,3,4')"),
    exclude_subs: bool = Query(True, description="Exclude substitute players (default: true)"),
    min_games: int = Query(1, ge=1, description="Minimum games played on machine"),
    sort_by: str = Query("games_played", description="Sort field: games_played, avg_score, best_score, win_percentage"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get performance statistics for a team across different machines.

    Example queries:
    - `/teams/SKP/machines` - All machines SKP has played (excludes subs by default)
    - `/teams/SKP/machines?seasons=22` - Season 22 only
    - `/teams/SKP/machines?seasons=21&seasons=22` - Seasons 21 and 22
    - `/teams/SKP/machines?venue_key=T4B` - T4B venue only
    - `/teams/SKP/machines?rounds=2,4` - Only rounds 2 and 4
    - `/teams/SKP/machines?min_games=5` - Only machines with 5+ games played
    - `/teams/SKP/machines?exclude_subs=false` - Include substitute players
    """
    # Validate sort parameters
    valid_sort_fields = ["games_played", "avg_score", "best_score", "win_percentage", "median_score"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of: {valid_sort_fields}")

    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")

    # Parse rounds filter
    rounds_list = None
    if rounds:
        try:
            rounds_list = [int(r.strip()) for r in rounds.split(',')]
            if not all(1 <= r <= 4 for r in rounds_list):
                raise ValueError()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid rounds parameter. Must be comma-separated integers 1-4")

    # First verify team exists
    team_check = execute_query(
        "SELECT 1 FROM teams WHERE team_key = :team_key LIMIT 1",
        {'team_key': team_key}
    )
    if not team_check:
        raise HTTPException(status_code=404, detail=f"Team '{team_key}' not found")

    # Build WHERE clause for filtering
    where_clauses = ["s.team_key = :team_key"]
    params = {'team_key': team_key}

    if seasons is not None and len(seasons) > 0:
        season_placeholders = ', '.join([f':season_{i}' for i in range(len(seasons))])
        where_clauses.append(f"s.season IN ({season_placeholders})")
        for i, season in enumerate(seasons):
            params[f'season_{i}'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if rounds_list is not None and len(rounds_list) > 0:
        placeholders = ', '.join([f':round_{i}' for i in range(len(rounds_list))])
        where_clauses.append(f"s.round_number IN ({placeholders})")
        for i, r in enumerate(rounds_list):
            params[f'round_{i}'] = r

    if exclude_subs:
        where_clauses.append("(s.is_substitute IS NULL OR s.is_substitute = false)")

    where_clause = " AND ".join(where_clauses)

    # Fetch all scores grouped by machine
    query = f"""
        SELECT
            s.machine_key,
            m.machine_name,
            t.team_name,
            s.season,
            s.venue_key,
            s.round_number,
            s.score
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        JOIN teams t ON s.team_key = t.team_key AND s.season = t.season
        WHERE {where_clause}
        ORDER BY s.machine_key, s.score
    """

    scores = execute_query(query, params)

    # Group scores by machine
    machine_scores = defaultdict(lambda: {'scores': [], 'rounds': set()})
    machine_info = {}

    for score in scores:
        mk = score['machine_key']
        machine_scores[mk]['scores'].append(score['score'])
        machine_scores[mk]['rounds'].add(score['round_number'])
        if mk not in machine_info:
            machine_info[mk] = {
                'machine_key': mk,
                'machine_name': score['machine_name'],
                'team_name': score['team_name'],
                'season': score['season'],
                'venue_key': venue_key if venue_key else score['venue_key']
            }

    # Calculate win percentages for this team
    win_percentages = calculate_team_win_percentage(team_key, seasons, venue_key, rounds_list, exclude_subs)

    # Calculate stats for each machine
    all_stats = []
    for machine_key, data in machine_scores.items():
        score_list = data['scores']
        if len(score_list) < min_games:
            continue

        info = machine_info[machine_key]
        scores_array = np.array(score_list)

        stat = {
            'team_key': team_key,
            'team_name': info['team_name'],
            'machine_key': machine_key,
            'machine_name': info['machine_name'],
            'venue_key': info['venue_key'],
            'season': info['season'],
            'games_played': len(score_list),
            'total_score': int(np.sum(scores_array)),
            'median_score': int(np.median(scores_array)),
            'avg_score': int(np.mean(scores_array)),
            'best_score': int(np.max(scores_array)),
            'worst_score': int(np.min(scores_array)),
            'median_percentile': None,  # Would need percentile data
            'avg_percentile': None,
            'win_percentage': win_percentages.get(machine_key),
            'rounds_played': sorted(list(data['rounds']))
        }
        all_stats.append(stat)

    # Sort results
    if sort_by == 'win_percentage':
        # Handle None values by putting them at the end
        all_stats.sort(
            key=lambda x: (x['win_percentage'] is None, x['win_percentage'] if x['win_percentage'] is not None else 0),
            reverse=(sort_order.lower() == 'desc')
        )
    else:
        all_stats.sort(
            key=lambda x: (x[sort_by] is None, x[sort_by] if x[sort_by] is not None else 0),
            reverse=(sort_order.lower() == 'desc')
        )

    # Apply pagination
    total = len(all_stats)
    paginated_stats = all_stats[offset:offset + limit]

    return TeamMachineStatsList(
        stats=[TeamMachineStats(**stat) for stat in paginated_stats],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{team_key}/players",
    response_model=TeamPlayerList,
    responses={404: {"model": ErrorResponse}},
    summary="Get team roster with statistics",
    description="Get all players who have played for a team with their statistics"
)
def get_team_players(
    team_key: str,
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue for statistics"),
    exclude_subs: bool = Query(True, description="Exclude substitute players (default: true)"),
):
    """
    Get all players who have played for a team with their statistics.

    Example queries:
    - `/teams/SKP/players` - All players who have played for SKP
    - `/teams/SKP/players?season=22` - Players who played for SKP in season 22
    - `/teams/SKP/players?venue_key=T4B` - Players with stats filtered to T4B venue
    """
    # First verify team exists
    team_check = execute_query(
        "SELECT 1 FROM teams WHERE team_key = :team_key LIMIT 1",
        {'team_key': team_key}
    )
    if not team_check:
        raise HTTPException(status_code=404, detail=f"Team '{team_key}' not found")

    # Build WHERE clause for player selection
    where_clauses = ["team_scores.team_key = :team_key"]
    params = {'team_key': team_key}

    if season is not None:
        where_clauses.append("team_scores.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("team_scores.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if exclude_subs:
        where_clauses.append("(team_scores.is_substitute IS NULL OR team_scores.is_substitute = false)")

    where_clause = " AND ".join(where_clauses)

    # Get player basic stats (games played, seasons)
    # Note: Using STRING_AGG for PostgreSQL (GROUP_CONCAT equivalent in MySQL)
    player_stats_query = f"""
        SELECT
            s.player_key,
            p.name as player_name,
            p.current_ipr,
            COUNT(*) as games_played,
            STRING_AGG(DISTINCT s.season::text, ',') as seasons
        FROM scores s
        JOIN players p ON s.player_key = p.player_key
        WHERE s.team_key = :team_key
            {f"AND s.season = :season" if season is not None else ""}
            {f"AND s.venue_key = :venue_key" if venue_key is not None else ""}
            {f"AND (s.is_substitute IS NULL OR s.is_substitute = false)" if exclude_subs else ""}
        GROUP BY s.player_key, p.name, p.current_ipr
    """

    player_stats = execute_query(player_stats_query, params)

    # Get win percentages using optimized batch query
    win_stats_where = where_clause.replace("team_scores.", "ts.")
    if exclude_subs:
        win_stats_where += " AND (os.is_substitute IS NULL OR os.is_substitute = false)"

    win_stats_query = f"""
        SELECT
            ts.player_key,
            COUNT(*) as total_comparisons,
            SUM(CASE WHEN ts.score > os.score THEN 1 ELSE 0 END) as wins
        FROM scores ts
        INNER JOIN scores os
            ON ts.match_key = os.match_key
            AND ts.round_number = os.round_number
            AND ts.machine_key = os.machine_key
            AND ts.team_key != os.team_key
        WHERE {win_stats_where}
        GROUP BY ts.player_key
    """

    win_stats = execute_query(win_stats_query, params)
    win_pct_map = {row['player_key']: (row['wins'] / row['total_comparisons'] * 100.0) if row['total_comparisons'] > 0 else None for row in win_stats}

    # Get most played machine per player using optimized query
    machine_stats_query = f"""
        SELECT
            s.player_key,
            s.machine_key,
            m.machine_name,
            COUNT(*) as games_played,
            ROW_NUMBER() OVER (PARTITION BY s.player_key ORDER BY COUNT(*) DESC) as rn
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE s.team_key = :team_key
            {f"AND s.season = :season" if season is not None else ""}
            {f"AND s.venue_key = :venue_key" if venue_key is not None else ""}
            {f"AND (s.is_substitute IS NULL OR s.is_substitute = false)" if exclude_subs else ""}
        GROUP BY s.player_key, s.machine_key, m.machine_name
    """

    machine_stats = execute_query(machine_stats_query, params)
    most_played_map = {}
    for row in machine_stats:
        if row['rn'] == 1 or row['player_key'] not in most_played_map:  # Get first (most played)
            most_played_map[row['player_key']] = {
                'machine_key': row['machine_key'],
                'machine_name': row['machine_name'],
                'games': row['games_played']
            }

    # Build player list
    players = []
    for player_stat in player_stats:
        player_key = player_stat['player_key']
        most_played = most_played_map.get(player_key, {})

        # Parse seasons (STRING_AGG returns comma-separated string)
        seasons_str = player_stat.get('seasons', '')
        seasons_played = sorted([int(s) for s in seasons_str.split(',') if s]) if seasons_str else []

        players.append({
            'player_key': player_key,
            'player_name': player_stat['player_name'],
            'current_ipr': player_stat['current_ipr'],
            'games_played': player_stat['games_played'],
            'win_percentage': win_pct_map.get(player_key),
            'most_played_machine_key': most_played.get('machine_key'),
            'most_played_machine_name': most_played.get('machine_name'),
            'most_played_machine_games': most_played.get('games', 0),
            'seasons_played': seasons_played
        })

    # Sort by games played descending
    players.sort(key=lambda x: x['games_played'], reverse=True)

    return TeamPlayerList(
        players=[TeamPlayer(**player) for player in players],
        total=len(players)
    )
