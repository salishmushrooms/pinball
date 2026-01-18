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
    PlayerDashboardStats,
    IPRDistribution,
    PlayerHighlight,
    GamePlayer,
    PlayerMachineGame,
    PlayerMachineGamesList,
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

    This implementation uses a batch query approach to avoid N+1 queries.
    Instead of querying opponent scores for each player score individually,
    we fetch all relevant round data in a single query.

    Args:
        player_key: Player's unique key
        seasons: Optional list of seasons to filter
        venue_key: Optional venue filter

    Returns:
        Dict mapping machine_key to win percentage (0-100)
    """
    # Build WHERE clause for filtering player's games
    where_clauses = ["ps.player_key = :player_key"]
    params = {'player_key': player_key}

    if seasons is not None and len(seasons) > 0:
        placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
        where_clauses.append(f"ps.season IN ({placeholders})")
        for i, season in enumerate(seasons):
            params[f'season{i}'] = season

    if venue_key is not None:
        where_clauses.append("ps.venue_key = :venue_key")
        params['venue_key'] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Single batch query: fetch player's scores along with all scores from the same rounds
    # This eliminates N+1 by joining player scores with all round scores in one query
    batch_query = f"""
        WITH player_games AS (
            SELECT
                ps.score_id,
                ps.machine_key,
                ps.score AS player_score,
                ps.match_key,
                ps.round_number,
                ps.player_position AS player_pos
            FROM scores ps
            WHERE {where_clause}
        )
        SELECT
            pg.machine_key,
            pg.player_score,
            pg.match_key,
            pg.round_number,
            pg.player_pos,
            rs.player_position AS other_pos,
            rs.score AS other_score
        FROM player_games pg
        JOIN scores rs ON
            rs.match_key = pg.match_key
            AND rs.round_number = pg.round_number
            AND rs.machine_key = pg.machine_key
            AND rs.player_position != pg.player_pos
        ORDER BY pg.match_key, pg.round_number, pg.player_pos
    """

    all_comparisons = execute_query(batch_query, params)

    # Process all comparisons in memory
    machine_wins = defaultdict(lambda: {'wins': 0, 'total': 0})

    for row in all_comparisons:
        machine_key = row['machine_key']
        player_score = row['player_score']
        round_number = row['round_number']
        player_pos = row['player_pos']
        other_pos = row['other_pos']
        other_score = row['other_score']

        # Determine if this is an opponent based on round type and position
        is_doubles = round_number in [1, 4]

        is_opponent = False
        if is_doubles:
            # 4-player rounds: positions 1&3 vs 2&4
            # Odd positions (1, 3) are teammates, even positions (2, 4) are teammates
            player_is_odd = player_pos % 2 == 1
            other_is_odd = other_pos % 2 == 1
            # They're opponents if one is odd and the other is even
            is_opponent = player_is_odd != other_is_odd
        else:
            # 2-player rounds: position 1 vs 2
            # Anyone in the round who isn't the player is an opponent
            is_opponent = True

        if is_opponent:
            machine_wins[machine_key]['total'] += 1
            if player_score > other_score:
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
    "/dashboard-stats",
    response_model=PlayerDashboardStats,
    summary="Get player dashboard statistics",
    description="Get statistics for the players page dashboard including total count, IPR distribution, new players, and random highlights"
)
def get_player_dashboard_stats():
    """
    Get dashboard statistics for the players page.

    Returns:
    - total_players: Total number of players
    - ipr_distribution: Count of players by IPR level (1-6)
    - new_players_count: Players first seen in latest season
    - latest_season: The latest season number
    - player_highlights: List of 5-7 random IPR 6 players with their best machine/score from latest season
    """
    import random

    # Get total players count
    total_query = "SELECT COUNT(*) as total FROM players"
    total_result = execute_query(total_query)
    total_players = total_result[0]['total'] if total_result else 0

    # Get latest season
    latest_season_query = "SELECT MAX(season) as latest FROM scores"
    latest_season_result = execute_query(latest_season_query)
    latest_season = latest_season_result[0]['latest'] if latest_season_result else 22

    # Get IPR distribution (grouped into levels 1-6)
    # current_ipr is already stored as the IPR level (1-6), not the raw score
    ipr_dist_query = """
        SELECT
            COALESCE(current_ipr, 0) as ipr_level,
            COUNT(*) as count
        FROM players
        GROUP BY current_ipr
        ORDER BY current_ipr
    """
    ipr_dist_result = execute_query(ipr_dist_query)
    ipr_distribution = [IPRDistribution(ipr_level=int(row['ipr_level']), count=row['count']) for row in ipr_dist_result]

    # Get new players count (first seen in latest season)
    new_players_query = """
        SELECT COUNT(*) as count
        FROM players
        WHERE first_seen_season = :latest_season
    """
    new_players_result = execute_query(new_players_query, {'latest_season': latest_season})
    new_players_count = new_players_result[0]['count'] if new_players_result else 0

    # Get random IPR 6 player highlights (5-7 players)
    player_highlights = []

    # Get all IPR 6 players (current_ipr stores the IPR level 1-6, not the raw rating)
    ipr6_players_query = """
        SELECT player_key, name, current_ipr
        FROM players
        WHERE current_ipr = 6
    """
    ipr6_players = execute_query(ipr6_players_query)

    if ipr6_players:
        # Randomly select 5-7 players (or all if fewer than 5)
        num_highlights = min(7, max(5, len(ipr6_players)))
        selected_players = random.sample(ipr6_players, min(num_highlights, len(ipr6_players)))

        # Get list of selected player keys for batch queries
        selected_player_keys = [p['player_key'] for p in selected_players]

        # BATCH QUERY 1: Get team/venue for ALL selected players at once (eliminates N+1)
        # Uses DISTINCT ON to get the most frequent team/venue per player
        team_venue_batch_query = """
            WITH player_team_counts AS (
                SELECT
                    s.player_key,
                    s.team_key,
                    t.team_name,
                    s.venue_key,
                    v.venue_name,
                    COUNT(*) as game_count,
                    ROW_NUMBER() OVER (PARTITION BY s.player_key ORDER BY COUNT(*) DESC) as rn
                FROM scores s
                JOIN teams t ON s.team_key = t.team_key AND s.season = t.season
                JOIN venues v ON s.venue_key = v.venue_key
                WHERE s.player_key = ANY(:player_keys)
                  AND s.season = :latest_season
                GROUP BY s.player_key, s.team_key, t.team_name, s.venue_key, v.venue_name
            )
            SELECT player_key, team_key, team_name, venue_key, venue_name
            FROM player_team_counts
            WHERE rn = 1
        """
        team_venue_results = execute_query(team_venue_batch_query, {
            'player_keys': selected_player_keys,
            'latest_season': latest_season
        })

        # Index team/venue results by player_key for O(1) lookup
        player_team_venue = {row['player_key']: row for row in team_venue_results}

        # BATCH QUERY 2: Get best machine/score for ALL selected players at once (eliminates N+1)
        # Uses window function to rank each player's scores by percentile
        best_machine_batch_query = """
            WITH player_scores AS (
                SELECT
                    s.player_key,
                    s.machine_key,
                    m.machine_name,
                    s.score,
                    (
                        SELECT MAX(p.percentile)
                        FROM score_percentiles p
                        WHERE p.machine_key = s.machine_key
                          AND p.venue_key = :venue_all
                          AND p.season = s.season
                          AND s.score >= p.score_threshold
                    ) as percentile
                FROM scores s
                JOIN machines m ON s.machine_key = m.machine_key
                WHERE s.player_key = ANY(:player_keys)
                  AND s.season = :latest_season
            ),
            ranked_scores AS (
                SELECT
                    player_key,
                    machine_key,
                    machine_name,
                    score,
                    COALESCE(percentile, 0) as percentile,
                    ROW_NUMBER() OVER (
                        PARTITION BY player_key
                        ORDER BY COALESCE(percentile, 0) DESC, score DESC
                    ) as rn
                FROM player_scores
            )
            SELECT player_key, machine_key, machine_name, score, percentile
            FROM ranked_scores
            WHERE rn = 1
        """
        best_machine_results = execute_query(best_machine_batch_query, {
            'player_keys': selected_player_keys,
            'latest_season': latest_season,
            'venue_all': '_ALL_'
        })

        # Index best machine results by player_key for O(1) lookup
        player_best_machine = {row['player_key']: row for row in best_machine_results}

        # Build highlights from batch results (no more N+1 queries!)
        for selected_player in selected_players:
            player_key = selected_player['player_key']

            # Lookup team/venue from batch result
            team_venue = player_team_venue.get(player_key, {})
            team_key = team_venue.get('team_key')
            team_name = team_venue.get('team_name')
            venue_key = team_venue.get('venue_key')
            venue_name = team_venue.get('venue_name')

            # Lookup best machine from batch result
            best = player_best_machine.get(player_key)

            if best:
                player_highlights.append(PlayerHighlight(
                    player_key=player_key,
                    player_name=selected_player['name'],
                    team_key=team_key,
                    team_name=team_name,
                    venue_key=venue_key,
                    venue_name=venue_name,
                    ipr=selected_player['current_ipr'],
                    season=latest_season,
                    best_machine_key=best['machine_key'],
                    best_machine_name=best['machine_name'],
                    best_score=best['score'],
                    best_percentile=best['percentile']
                ))

    return PlayerDashboardStats(
        total_players=total_players,
        ipr_distribution=ipr_distribution,
        new_players_count=new_players_count,
        latest_season=latest_season,
        player_highlights=player_highlights
    )


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

    player = players[0]

    # Get current team from most recent season's scores (non-substitute appearances)
    current_team_query = """
        SELECT s.team_key, t.team_name
        FROM scores s
        JOIN teams t ON s.team_key = t.team_key AND s.season = t.season
        WHERE s.player_key = :player_key
          AND s.season = :last_season
          AND s.is_substitute = false
        GROUP BY s.team_key, t.team_name
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """
    team_result = execute_query(current_team_query, {
        'player_key': player_key,
        'last_season': player['last_seen_season']
    })

    if team_result:
        player['current_team_key'] = team_result[0]['team_key']
        player['current_team_name'] = team_result[0]['team_name']
    else:
        player['current_team_key'] = None
        player['current_team_name'] = None

    return PlayerDetail(**player)


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


@router.get(
    "/{player_key}/machines/{machine_key}/games",
    response_model=PlayerMachineGamesList,
    responses={404: {"model": ErrorResponse}},
    summary="Get player's games on a specific machine with opponent details",
    description="Get all individual games for a player on a specific machine, including all players and their scores"
)
def get_player_machine_games(
    player_key: str,
    machine_key: str,
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    seasons: Union[TypingList[int], None] = Query(None, description="Filter by season(s) - can pass multiple"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Get all individual games for a player on a specific machine with complete opponent details.

    Returns a list of games showing:
    - Match details (season, week, date, venue)
    - All players in each game with their scores, positions, and teams
    - Home and away team information

    Example: `/players/sean_irby/machines/MM/games`
    Example: `/players/sean_irby/machines/MM/games?seasons=21&seasons=22&venue_key=KRA`
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

    # Build WHERE clause for player's games
    where_clauses = [
        "ps.player_key = :player_key",
        "ps.machine_key = :machine_key"
    ]
    params = {
        'player_key': player_key,
        'machine_key': machine_key
    }

    if venue_key is not None:
        where_clauses.append("ps.venue_key = :venue_key")
        params['venue_key'] = venue_key

    if seasons is not None and len(seasons) > 0:
        placeholders = ','.join([f':season{i}' for i in range(len(seasons))])
        where_clauses.append(f"ps.season IN ({placeholders})")
        for i, season in enumerate(seasons):
            params[f'season{i}'] = season

    where_clause = " AND ".join(where_clauses)

    # Get total count
    count_query = f"""
        SELECT COUNT(DISTINCT ps.match_key || '-' || ps.round_number) as total
        FROM scores ps
        WHERE {where_clause}
    """
    count_result = execute_query(count_query, params)
    total = count_result[0]['total'] if count_result else 0

    # Fetch all games for this player on this machine
    # Include limit and offset for pagination
    games_query = f"""
        WITH player_games AS (
            SELECT DISTINCT
                ps.match_key,
                ps.round_number,
                ps.season,
                ps.week,
                ps.date,
                ps.venue_key,
                v.venue_name,
                m.home_team_key,
                m.away_team_key
            FROM scores ps
            JOIN venues v ON ps.venue_key = v.venue_key
            JOIN matches m ON ps.match_key = m.match_key
            WHERE {where_clause}
            ORDER BY ps.season DESC, ps.week DESC, ps.date DESC, ps.match_key, ps.round_number
            LIMIT :limit OFFSET :offset
        )
        SELECT
            pg.match_key,
            pg.round_number,
            pg.season,
            pg.week,
            pg.date,
            pg.venue_key,
            pg.venue_name,
            pg.home_team_key,
            ht.team_name as home_team_name,
            pg.away_team_key,
            at.team_name as away_team_name,
            s.player_key,
            p.name as player_name,
            s.player_position,
            s.score,
            s.team_key,
            st.team_name as player_team_name,
            s.is_home_team
        FROM player_games pg
        JOIN scores s ON s.match_key = pg.match_key
            AND s.round_number = pg.round_number
            AND s.machine_key = :machine_key
        JOIN players p ON s.player_key = p.player_key
        JOIN teams ht ON pg.home_team_key = ht.team_key AND pg.season = ht.season
        JOIN teams at ON pg.away_team_key = at.team_key AND pg.season = at.season
        JOIN teams st ON s.team_key = st.team_key AND pg.season = st.season
        ORDER BY pg.season DESC, pg.week DESC, pg.date DESC, pg.match_key, pg.round_number, s.player_position
    """

    params['limit'] = limit
    params['offset'] = offset

    results = execute_query(games_query, params)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No games found for player '{player_key}' on machine '{machine_key}'"
        )

    # Group results by game (match_key + round_number)
    from collections import defaultdict
    games_dict = defaultdict(lambda: {
        'match_key': None,
        'season': None,
        'week': None,
        'date': None,
        'venue_key': None,
        'venue_name': None,
        'round_number': None,
        'home_team_key': None,
        'home_team_name': None,
        'away_team_key': None,
        'away_team_name': None,
        'players': []
    })

    for row in results:
        game_key = f"{row['match_key']}-{row['round_number']}"

        if games_dict[game_key]['match_key'] is None:
            games_dict[game_key] = {
                'match_key': row['match_key'],
                'season': row['season'],
                'week': row['week'],
                'date': row['date'].isoformat() if row['date'] else None,
                'venue_key': row['venue_key'],
                'venue_name': row['venue_name'],
                'round_number': row['round_number'],
                'home_team_key': row['home_team_key'],
                'home_team_name': row['home_team_name'],
                'away_team_key': row['away_team_key'],
                'away_team_name': row['away_team_name'],
                'players': []
            }

        games_dict[game_key]['players'].append({
            'player_key': row['player_key'],
            'player_name': row['player_name'],
            'player_position': row['player_position'],
            'score': row['score'],
            'team_key': row['team_key'],
            'team_name': row['player_team_name'],
            'is_home_team': row['is_home_team']
        })

    # Convert to list and create response objects
    games_list = []
    for game_data in games_dict.values():
        game_players = [GamePlayer(**player) for player in game_data['players']]
        games_list.append(PlayerMachineGame(
            match_key=game_data['match_key'],
            season=game_data['season'],
            week=game_data['week'],
            date=game_data['date'],
            venue_key=game_data['venue_key'],
            venue_name=game_data['venue_name'],
            round_number=game_data['round_number'],
            home_team_key=game_data['home_team_key'],
            home_team_name=game_data['home_team_name'],
            away_team_key=game_data['away_team_key'],
            away_team_name=game_data['away_team_name'],
            players=game_players
        ))

    return PlayerMachineGamesList(
        player_key=player_key,
        player_name=player_name,
        machine_key=machine_key,
        machine_name=machine_name,
        games=games_list,
        total=total,
        limit=limit,
        offset=offset
    )
