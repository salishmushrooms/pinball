"""
Players API endpoints
"""
from typing import Optional, Dict, List as TypingList, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from collections import defaultdict

from api.models.schemas import (
    PlayerBase,
    PlayerDetail,
    PlayerList,
    PlayerMachineStats,
    PlayerMachineStatsList,
    PlayerMachineScoreHistoryResponse,
    ErrorResponse
)
from api.dependencies import execute_query
from etl.database import db

router = APIRouter(prefix="/players", tags=["players"])


def calculate_stats_from_scores(
    player_key: str,
    seasons: Optional[TypingList[int]] = None,
    venue_key: Optional[str] = None,
    min_games: int = 1
) -> TypingList[Dict]:
    """
    Calculate player machine stats from raw scores (for venue filtering).

    Args:
        player_key: Player's unique key
        seasons: Optional list of seasons to filter
        venue_key: Optional venue filter
        min_games: Minimum games played

    Returns:
        List of stat dictionaries
    """
    import numpy as np

    # Build WHERE clause
    where_clauses = ["s.player_key = :player_key"]
    params = {'player_key': player_key}

    if seasons is not None and len(seasons) > 0:
        placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
        where_clauses.append(f"s.season IN ({placeholders})")
        for i, season in enumerate(seasons):
            params[f'season{i}'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Fetch all scores grouped by machine
    query = f"""
        SELECT
            s.machine_key,
            m.machine_name,
            s.season,
            s.venue_key,
            s.score
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE {where_clause}
        ORDER BY s.machine_key, s.score
    """

    scores = execute_query(query, params)

    # Group scores by machine
    machine_scores = defaultdict(list)
    machine_info = {}

    for score in scores:
        mk = score['machine_key']
        machine_scores[mk].append(score['score'])
        if mk not in machine_info:
            machine_info[mk] = {
                'machine_key': mk,
                'machine_name': score['machine_name'],
                'season': score['season'],
                'venue_key': venue_key if venue_key else score['venue_key']  # Use filter venue or actual venue
            }

    # Calculate stats for each machine
    stats = []
    for machine_key, score_list in machine_scores.items():
        if len(score_list) < min_games:
            continue

        info = machine_info[machine_key]
        scores_array = np.array(score_list)

        stat = {
            'player_key': player_key,
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
        }
        stats.append(stat)

    return stats


def calculate_win_percentage_for_player(
    player_key: str,
    seasons: Optional[TypingList[int]] = None,
    venue_key: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate win percentage for a player on each machine.

    Win percentage is calculated by comparing player's score to opponents:
    - Rounds 1 & 4 (doubles): Even positions vs odd positions (2 opponents each)
    - Rounds 2 & 3 (singles): 1 opponent

    Args:
        player_key: Player's unique key
        seasons: Optional list of seasons to filter
        venue_key: Optional venue filter

    Returns:
        Dict mapping machine_key to win percentage (0-100)
    """
    # Build WHERE clause for filtering
    where_clauses = ["s.player_key = :player_key"]
    params = {'player_key': player_key}

    if seasons is not None and len(seasons) > 0:
        placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
        where_clauses.append(f"s.season IN ({placeholders})")
        for i, season in enumerate(seasons):
            params[f'season{i}'] = season

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Fetch all scores for this player with match context
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

    player_scores = execute_query(query, params)

    # For each score, we need to fetch opponent scores from same match/round
    machine_wins = defaultdict(lambda: {'wins': 0, 'total': 0})

    for score_record in player_scores:
        machine_key = score_record['machine_key']
        match_key = score_record['match_key']
        round_number = score_record['round_number']
        player_position = score_record['player_position']
        player_score = score_record['score']
        player_team = score_record['team_key']

        # Fetch all scores from this match/round/machine
        round_query = """
            SELECT player_position, score, team_key
            FROM scores
            WHERE match_key = :match_key
            AND round_number = :round_number
            AND machine_key = :machine_key
            ORDER BY player_position
        """
        round_scores = execute_query(round_query, {
            'match_key': match_key,
            'round_number': round_number,
            'machine_key': machine_key
        })

        # Determine opponents based on round type and position
        # Rounds 1 & 4 are doubles (4 players): positions 1&3 vs 2&4
        # Rounds 2 & 3 are singles (2 players): position 1 vs 2
        is_doubles = round_number in [1, 4]

        opponent_scores = []
        for rs in round_scores:
            # Skip the player themselves
            if rs['player_position'] == player_position:
                continue

            # Determine if this is an opponent based on position
            if is_doubles:
                # 4-player rounds: positions 1&3 vs 2&4
                # Odd positions (1, 3) are teammates, even positions (2, 4) are teammates
                player_is_odd = player_position % 2 == 1
                other_is_odd = rs['player_position'] % 2 == 1

                # They're opponents if one is odd and the other is even
                if player_is_odd != other_is_odd:
                    opponent_scores.append(rs['score'])
            else:
                # 2-player rounds: position 1 vs 2
                # Anyone in the round who isn't the player is an opponent
                opponent_scores.append(rs['score'])

        # Compare player's score to each opponent
        for opp_score in opponent_scores:
            machine_wins[machine_key]['total'] += 1
            if player_score > opp_score:
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
    seasons: Union[TypingList[int], None] = Query(None, description="Filter by season(s) - can pass multiple"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    min_games: int = Query(1, ge=1, description="Minimum games played on machine"),
    sort_by: str = Query("median_percentile", description="Sort field: median_percentile, avg_percentile, games_played, avg_score, best_score, win_percentage"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get performance statistics for a player across different machines.

    Example queries:
    - `/players/sean_irby/machines` - All machines Sean has played
    - `/players/sean_irby/machines?seasons=22` - Season 22 only
    - `/players/sean_irby/machines?seasons=21&seasons=22` - Seasons 21 and 22
    - `/players/sean_irby/machines?venue_key=KRA` - Kraken venue only
    - `/players/sean_irby/machines?min_games=5` - Only machines with 5+ games played
    - `/players/sean_irby/machines?sort_by=win_percentage&sort_order=desc` - Sort by win percentage
    """
    # Validate sort parameters
    valid_sort_fields = ["median_percentile", "avg_percentile", "games_played", "avg_score", "best_score", "win_percentage"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by field. Must be one of: {valid_sort_fields}")

    if sort_order.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")

    # First verify player exists
    player_check = execute_query("SELECT 1 FROM players WHERE player_key = :player_key", {'player_key': player_key})
    if not player_check:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    # Calculate win percentages for this player (with filters applied)
    win_percentages = calculate_win_percentage_for_player(player_key, seasons, venue_key)

    # If filtering by specific venue, calculate stats from raw scores
    # Otherwise use pre-aggregated player_machine_stats table
    if venue_key is not None:
        # Calculate from raw scores
        all_stats = calculate_stats_from_scores(player_key, seasons, venue_key, min_games)

        # Add player_name to each stat
        player_name_query = "SELECT name FROM players WHERE player_key = :player_key"
        player_name_result = execute_query(player_name_query, {'player_key': player_key})
        player_name = player_name_result[0]['name'] if player_name_result else None

        for stat in all_stats:
            stat['player_name'] = player_name
    else:
        # Try to use pre-aggregated stats first
        where_clauses = ["pms.player_key = :player_key", "pms.games_played >= :min_games"]
        params = {'player_key': player_key, 'min_games': min_games}

        if seasons is not None and len(seasons) > 0:
            placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
            where_clauses.append(f"pms.season IN ({placeholders})")
            for i, season in enumerate(seasons):
                params[f'season{i}'] = season

        # For no venue filter, use _ALL_ aggregate
        where_clauses.append("pms.venue_key = '_ALL_'")

        where_clause = " AND ".join(where_clauses)

        # Get all results (we'll sort in Python since win_percentage isn't in the table)
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
        """
        all_stats = execute_query(query, params)

        # Check if we need to calculate stats for missing seasons
        # This handles cases where player_machine_stats table hasn't been populated for certain seasons
        if seasons is not None and len(seasons) > 0:
            # Find which seasons have aggregated data
            seasons_with_data = set(stat['season'] for stat in all_stats)
            missing_seasons = [s for s in seasons if s not in seasons_with_data]

            if missing_seasons:
                # Calculate stats from raw scores for missing seasons
                raw_stats = calculate_stats_from_scores(player_key, missing_seasons, venue_key=None, min_games=min_games)

                # Add player_name to raw stats
                player_name_query = "SELECT name FROM players WHERE player_key = :player_key"
                player_name_result = execute_query(player_name_query, {'player_key': player_key})
                player_name = player_name_result[0]['name'] if player_name_result else None

                for stat in raw_stats:
                    stat['player_name'] = player_name

                # Combine aggregated and raw stats
                all_stats.extend(raw_stats)
        elif not all_stats:
            # No season filter and no aggregated data - calculate from all raw scores
            all_stats = calculate_stats_from_scores(player_key, seasons, venue_key=None, min_games=min_games)

            # Add player_name to each stat
            player_name_query = "SELECT name FROM players WHERE player_key = :player_key"
            player_name_result = execute_query(player_name_query, {'player_key': player_key})
            player_name = player_name_result[0]['name'] if player_name_result else None

            for stat in all_stats:
                stat['player_name'] = player_name

    # Add win_percentage to each stat
    for stat in all_stats:
        stat['win_percentage'] = win_percentages.get(stat['machine_key'])

    # Sort in Python
    if sort_by == 'win_percentage':
        # Handle None values by putting them at the end
        all_stats.sort(
            key=lambda x: (x['win_percentage'] is None, x['win_percentage'] if x['win_percentage'] is not None else 0),
            reverse=(sort_order.lower() == 'desc')
        )
    else:
        # Sort by database field
        all_stats.sort(
            key=lambda x: (x[sort_by] is None, x[sort_by] if x[sort_by] is not None else 0),
            reverse=(sort_order.lower() == 'desc')
        )

    # Apply pagination
    total = len(all_stats)
    paginated_stats = all_stats[offset:offset + limit]

    return PlayerMachineStatsList(
        stats=[PlayerMachineStats(**stat) for stat in paginated_stats],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get(
    "/{player_key}/machines/{machine_key}/scores",
    response_model=PlayerMachineScoreHistoryResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get player's score history on a specific machine",
    description="Get all individual scores for a player on a specific machine, grouped by season for trend analysis"
)
def get_player_machine_score_history(
    player_key: str,
    machine_key: str,
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    seasons: Union[TypingList[int], None] = Query(None, description="Filter by season(s) - can pass multiple")
):
    """
    Get all individual scores for a player on a specific machine.

    Returns scores grouped by season with statistics for candlestick/scatter charts.
    Useful for visualizing player progression over time.

    Example: `/players/sean_irby/machines/MM/scores`
    Example: `/players/sean_irby/machines/MM/scores?seasons=21&seasons=22`
    """
    # First verify player exists
    player_check = execute_query(
        "SELECT name FROM players WHERE player_key = :player_key",
        {'player_key': player_key}
    )
    if not player_check:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    player_name = player_check[0]['name']

    # Verify machine exists
    machine_check = execute_query(
        "SELECT machine_name FROM machines WHERE machine_key = :machine_key",
        {'machine_key': machine_key}
    )
    if not machine_check:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    machine_name = machine_check[0]['machine_name']

    # Build WHERE clause
    where_clauses = [
        "s.player_key = :player_key",
        "s.machine_key = :machine_key"
    ]
    params = {
        'player_key': player_key,
        'machine_key': machine_key
    }

    if venue_key is not None:
        where_clauses.append("s.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if seasons is not None and len(seasons) > 0:
        placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
        where_clauses.append(f"s.season IN ({placeholders})")
        for i, season in enumerate(seasons):
            params[f'season{i}'] = season

    where_clause = " AND ".join(where_clauses)

    # Fetch all scores with details
    query = f"""
        SELECT
            s.score,
            s.season,
            s.week,
            s.date,
            s.venue_key,
            v.venue_name,
            s.round_number,
            s.player_position,
            s.match_key
        FROM scores s
        JOIN venues v ON s.venue_key = v.venue_key
        WHERE {where_clause}
        ORDER BY s.season, s.week, s.date
    """

    scores = execute_query(query, params)

    if not scores:
        raise HTTPException(
            status_code=404,
            detail=f"No scores found for player '{player_key}' on machine '{machine_key}'"
        )

    # Group scores by season for aggregation
    import numpy as np
    from collections import defaultdict

    season_groups = defaultdict(list)
    all_scores_data = []

    for score_record in scores:
        season_num = score_record['season']
        score_val = score_record['score']
        season_groups[season_num].append(score_val)

        all_scores_data.append({
            'score': score_val,
            'season': season_num,
            'week': score_record['week'],
            'date': score_record['date'].isoformat() if score_record['date'] else None,
            'venue_key': score_record['venue_key'],
            'venue_name': score_record['venue_name'],
            'round_number': score_record['round_number'],
            'player_position': score_record['player_position'],
            'match_key': score_record['match_key']
        })

    # Calculate statistics per season (for candlestick view)
    season_stats = []
    for season_num in sorted(season_groups.keys()):
        scores_array = np.array(season_groups[season_num])
        season_stats.append({
            'season': season_num,
            'games_played': len(scores_array),
            'min_score': int(np.min(scores_array)),
            'max_score': int(np.max(scores_array)),
            'median_score': int(np.median(scores_array)),
            'mean_score': int(np.mean(scores_array)),
            'q1_score': int(np.percentile(scores_array, 25)),
            'q3_score': int(np.percentile(scores_array, 75))
        })

    return PlayerMachineScoreHistoryResponse(
        player_key=player_key,
        player_name=player_name,
        machine_key=machine_key,
        machine_name=machine_name,
        total_games=len(scores),
        scores=all_scores_data,
        season_stats=season_stats
    )
