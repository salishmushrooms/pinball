"""
Teams API endpoints
"""
from typing import Optional, List, Dict
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
    season: Optional[int] = None,
    venue_key: Optional[str] = None,
    rounds: Optional[List[int]] = None
) -> Dict[str, float]:
    """
    Calculate win percentage for a team on each machine.

    Win percentage is calculated by comparing team player scores to opponent scores.

    Args:
        team_key: Team's unique key
        season: Optional season filter
        venue_key: Optional venue filter
        rounds: Optional list of rounds to filter (1-4)

    Returns:
        Dict mapping machine_key to win percentage (0-100)
    """
    # Build WHERE clause for filtering
    where_clauses = ["s.team_key = :team_key"]
    params = {'team_key': team_key}

    if season is not None:
        where_clauses.append("s.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if rounds is not None and len(rounds) > 0:
        placeholders = ', '.join([f':round_{i}' for i in range(len(rounds))])
        where_clauses.append(f"s.round_number IN ({placeholders})")
        for i, r in enumerate(rounds):
            params[f'round_{i}'] = r

    where_clause = " AND ".join(where_clauses)

    # Fetch all scores for this team with match context
    query = f"""
        SELECT
            s.score_id,
            s.machine_key,
            s.score,
            s.match_key,
            s.round_number,
            s.player_position,
            s.team_key
        FROM scores s
        WHERE {where_clause}
        ORDER BY s.match_key, s.round_number
    """

    team_scores = execute_query(query, params)

    # For each score, fetch opponent scores from same match/round
    machine_wins = defaultdict(lambda: {'wins': 0, 'total': 0})

    for score_record in team_scores:
        machine_key = score_record['machine_key']
        match_key = score_record['match_key']
        round_number = score_record['round_number']
        player_score = score_record['score']

        # Fetch all scores from this match/round/machine for opponents
        round_query = """
            SELECT player_position, score, team_key
            FROM scores
            WHERE match_key = :match_key
            AND round_number = :round_number
            AND machine_key = :machine_key
            AND team_key != :team_key
            ORDER BY player_position
        """
        opponent_scores = execute_query(round_query, {
            'match_key': match_key,
            'round_number': round_number,
            'machine_key': machine_key,
            'team_key': team_key
        })

        # Compare team player's score to each opponent
        for opp in opponent_scores:
            machine_wins[machine_key]['total'] += 1
            if player_score > opp['score']:
                machine_wins[machine_key]['wins'] += 1

    # Calculate win percentages
    win_percentages = {}
    for machine_key, stats in machine_wins.items():
        if stats['total'] > 0:
            win_percentages[machine_key] = (stats['wins'] / stats['total']) * 100.0
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
    season: Optional[int] = Query(None, description="Filter by season"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    rounds: Optional[str] = Query(None, description="Filter by rounds (comma-separated, e.g., '1,2,3,4')"),
    min_games: int = Query(1, ge=1, description="Minimum games played on machine"),
    sort_by: str = Query("games_played", description="Sort field: games_played, avg_score, best_score, win_percentage"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get performance statistics for a team across different machines.

    Example queries:
    - `/teams/SKP/machines` - All machines SKP has played
    - `/teams/SKP/machines?season=22` - Season 22 only
    - `/teams/SKP/machines?venue_key=T4B` - T4B venue only
    - `/teams/SKP/machines?rounds=2,4` - Only rounds 2 and 4
    - `/teams/SKP/machines?min_games=5` - Only machines with 5+ games played
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

    if season is not None:
        where_clauses.append("s.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if rounds_list is not None and len(rounds_list) > 0:
        placeholders = ', '.join([f':round_{i}' for i in range(len(rounds_list))])
        where_clauses.append(f"s.round_number IN ({placeholders})")
        for i, r in enumerate(rounds_list):
            params[f'round_{i}'] = r

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
    win_percentages = calculate_team_win_percentage(team_key, season, venue_key, rounds_list)

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
    where_clauses = ["s.team_key = :team_key"]
    params = {'team_key': team_key}

    if season is not None:
        where_clauses.append("s.season = :season")
        params['season'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Get player stats
    query = f"""
        SELECT
            s.player_key,
            p.name as player_name,
            p.current_ipr,
            s.season,
            s.machine_key,
            m.machine_name,
            s.score,
            s.match_key,
            s.round_number
        FROM scores s
        JOIN players p ON s.player_key = p.player_key
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE {where_clause}
        ORDER BY s.player_key, s.machine_key
    """

    scores = execute_query(query, params)

    # Group by player
    player_data = defaultdict(lambda: {
        'player_name': None,
        'current_ipr': None,
        'games': 0,
        'wins': 0,
        'total_games': 0,
        'seasons': set(),
        'machine_games': defaultdict(int)
    })

    # Calculate per-player stats
    for score in scores:
        pk = score['player_key']
        player_data[pk]['player_name'] = score['player_name']
        player_data[pk]['current_ipr'] = score['current_ipr']
        player_data[pk]['games'] += 1
        player_data[pk]['seasons'].add(score['season'])
        player_data[pk]['machine_games'][score['machine_key']] += 1

        # For win percentage, need to compare to opponents in same match/round
        match_key = score['match_key']
        round_number = score['round_number']
        machine_key = score['machine_key']
        player_score = score['score']

        # Fetch opponent scores
        opp_query = """
            SELECT score
            FROM scores
            WHERE match_key = :match_key
            AND round_number = :round_number
            AND machine_key = :machine_key
            AND team_key != :team_key
        """
        opponents = execute_query(opp_query, {
            'match_key': match_key,
            'round_number': round_number,
            'machine_key': machine_key,
            'team_key': team_key
        })

        for opp in opponents:
            player_data[pk]['total_games'] += 1
            if player_score > opp['score']:
                player_data[pk]['wins'] += 1

    # Build player list
    players = []
    for player_key, data in player_data.items():
        # Find most played machine
        most_played_machine = None
        most_played_games = 0
        most_played_name = None

        for mk, games in data['machine_games'].items():
            if games > most_played_games:
                most_played_games = games
                most_played_machine = mk
                # Get machine name
                machine_query = "SELECT machine_name FROM machines WHERE machine_key = :mk"
                machine_result = execute_query(machine_query, {'mk': mk})
                if machine_result:
                    most_played_name = machine_result[0]['machine_name']

        win_pct = None
        if data['total_games'] > 0:
            win_pct = (data['wins'] / data['total_games']) * 100.0

        players.append({
            'player_key': player_key,
            'player_name': data['player_name'],
            'current_ipr': data['current_ipr'],
            'games_played': data['games'],
            'win_percentage': win_pct,
            'most_played_machine_key': most_played_machine,
            'most_played_machine_name': most_played_name,
            'most_played_machine_games': most_played_games,
            'seasons_played': sorted(list(data['seasons']))
        })

    # Sort by games played descending
    players.sort(key=lambda x: x['games_played'], reverse=True)

    return TeamPlayerList(
        players=[TeamPlayer(**player) for player in players],
        total=len(players)
    )
