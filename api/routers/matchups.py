"""
Matchup API endpoints for analyzing team vs team matchups
"""
from typing import Optional, List, Dict, Union
from fastapi import APIRouter, HTTPException, Query
import json
import math
from collections import defaultdict

from api.models.schemas import (
    MatchupAnalysis,
    MachinePickFrequency,
    PlayerMachinePreference,
    PlayerMachineConfidence,
    TeamMachineConfidence,
    ConfidenceInterval,
    MachineInfo,
    ErrorResponse
)
from api.dependencies import execute_query

router = APIRouter(prefix="/matchups", tags=["matchups"])


def get_current_machines_for_venue(venue_key: str, seasons: List[int]) -> List[str]:
    """
    Get the machine lineup for a venue from the database.
    Returns list of machine keys that are active at this venue for the most recent season requested.
    """
    try:
        # Get machines from venue_machines table for the most recent season in the list
        query = """
            SELECT vm.machine_key
            FROM venue_machines vm
            WHERE vm.venue_key = :venue_key
            AND vm.season = (
                SELECT MAX(season)
                FROM venue_machines
                WHERE venue_key = :venue_key
                AND season = ANY(:seasons)
            )
            AND vm.active = true
            ORDER BY vm.machine_key
        """
        results = execute_query(query, {'venue_key': venue_key, 'seasons': seasons})
        return [row['machine_key'] for row in results]
    except Exception:
        return []


def get_machine_names(machine_keys: List[str]) -> Dict[str, str]:
    """
    Get full machine names for a list of machine keys.
    Returns dict mapping machine_key -> machine_name.
    """
    if not machine_keys:
        return {}

    # First try database lookup
    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    results = execute_query(machine_names_query, {'machines': machine_keys})
    name_map = {m['machine_key']: m['machine_name'] for m in results}

    # Fall back to machine_variations.json for any missing
    missing_keys = [k for k in machine_keys if k not in name_map]
    if missing_keys:
        try:
            with open("machine_variations.json", 'r') as f:
                machine_variations = json.load(f)
                for key in missing_keys:
                    if key in machine_variations:
                        name_map[key] = machine_variations[key].get('name', key)
                    else:
                        name_map[key] = key
        except Exception:
            for key in missing_keys:
                name_map[key] = key

    return name_map


def calculate_confidence_interval(scores: List[float], confidence_level: float = 95.0) -> Optional[ConfidenceInterval]:
    """
    Calculate confidence interval for a list of scores.
    Returns None if insufficient data (< 5 scores).
    """
    if len(scores) < 5:
        return None

    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std_dev = math.sqrt(variance)

    # For 95% confidence, z-score is 1.96
    z_score = 1.96 if confidence_level == 95.0 else 1.645  # 90% fallback

    margin_of_error = z_score * (std_dev / math.sqrt(len(scores)))

    return ConfidenceInterval(
        mean=mean,
        std_dev=std_dev,
        lower_bound=max(0, mean - margin_of_error),  # Scores can't be negative
        upper_bound=mean + margin_of_error,
        sample_size=len(scores),
        confidence_level=confidence_level
    )


def get_team_machine_pick_frequency(
    team_key: str,
    team_home_venue: str,
    available_machines: List[str],
    seasons: List[int],
    is_home_team_at_venue: bool = True
) -> List[MachinePickFrequency]:
    """
    Calculate how often a team picks each machine across multiple seasons.
    Uses pre-calculated team_machine_picks table from the database.

    Strategy:
    - Gets ALL of the team's doubles picks from the database
    - Filters results to only show machines in available_machines (at target venue)
    - This provides better predictions by using more data while keeping results relevant

    The is_home_team_at_venue parameter is kept for compatibility but both home
    and away teams now use the same logic.
    """
    try:
        if not available_machines:
            return []

        # Query team_machine_picks table for doubles picks
        # Sum picks across all seasons and both home/away contexts
        query = """
            SELECT
                tmp.machine_key,
                m.machine_name,
                SUM(tmp.times_picked) as total_picked
            FROM team_machine_picks tmp
            INNER JOIN machines m ON tmp.machine_key = m.machine_key
            WHERE tmp.team_key = :team_key
            AND tmp.season = ANY(:seasons)
            AND tmp.round_type = 'doubles'
            AND tmp.machine_key = ANY(:machines)
            GROUP BY tmp.machine_key, m.machine_name
            ORDER BY total_picked DESC
        """

        results = execute_query(query, {
            'team_key': team_key,
            'seasons': seasons,
            'machines': available_machines
        })

        # Build result with 2x multiplier for doubles (to maintain compatibility)
        result = []
        for row in results:
            result.append(MachinePickFrequency(
                machine_key=row['machine_key'],
                machine_name=row['machine_name'],
                times_picked=row['total_picked'] * 2,  # 2x multiplier for doubles
                total_opportunities=0,  # Deprecated field
                pick_percentage=0.0  # Deprecated field
            ))

        return result

    except Exception as e:
        print(f"Error calculating pick frequency: {e}")
        return []


def get_player_machine_preferences(
    team_key: str,
    available_machines: List[str],
    seasons: List[int],
    roster_only: bool = True
) -> List[PlayerMachinePreference]:
    """
    Get each player's machine picking preferences on this team across multiple seasons.
    OPTIMIZED: Single query to get all player machine counts.

    Args:
        roster_only: If True (default), only include roster players (is_substitute = false)
    """
    if not available_machines:
        return []

    # Build the query with roster filtering
    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_only:
        roster_filter = "AND s.is_substitute = false"

    # Get all player-machine counts in a single query
    all_picks_query = f"""
        SELECT
            s.player_key,
            p.name as player_name,
            s.machine_key,
            m.machine_name,
            COUNT(*) as times_played
        FROM scores s
        INNER JOIN players p ON s.player_key = p.player_key
        INNER JOIN machines m ON s.machine_key = m.machine_key
        WHERE s.team_key = :team_key
            AND s.season = ANY(:seasons)
            AND s.machine_key = ANY(:machines)
            {roster_filter}
        GROUP BY s.player_key, p.name, s.machine_key, m.machine_name
        ORDER BY s.player_key, times_played DESC
    """

    all_picks = execute_query(all_picks_query, query_params)

    # Group by player
    player_picks = defaultdict(list)
    for pick in all_picks:
        player_key = pick['player_key']
        player_picks[player_key].append({
            'player_name': pick['player_name'],
            'machine_key': pick['machine_key'],
            'machine_name': pick['machine_name'],
            'times_played': pick['times_played']
        })

    # Build result
    result = []
    for player_key, picks in player_picks.items():
        if picks:
            player_name = picks[0]['player_name']
            top_machines = [
                MachinePickFrequency(
                    machine_key=pick['machine_key'],
                    machine_name=pick['machine_name'],
                    times_picked=pick['times_played'],
                    total_opportunities=pick['times_played'],  # Simplified
                    pick_percentage=100.0  # Simplified
                )
                for pick in picks[:5]  # Top 5
            ]

            result.append(PlayerMachinePreference(
                player_key=player_key,
                player_name=player_name,
                top_machines=top_machines
            ))

    return result


def get_player_machine_confidence(
    team_key: str,
    available_machines: List[str],
    seasons: List[int],
    roster_only: bool = True
) -> List[PlayerMachineConfidence]:
    """
    Get confidence intervals for each player on each available machine across multiple seasons.
    OPTIMIZED: Single query to fetch all scores at once.

    Args:
        roster_only: If True (default), only include roster players (is_substitute = false)
    """
    # Get all machine names in one query
    if not available_machines:
        return []

    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    machine_names = execute_query(machine_names_query, {'machines': available_machines})
    machine_name_map = {m['machine_key']: m['machine_name'] for m in machine_names}

    # Build query with roster filtering
    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_only:
        roster_filter = "AND s.is_substitute = false"

    # Get ALL scores for this team in a single query
    all_scores_query = f"""
        SELECT
            s.player_key,
            p.name as player_name,
            s.machine_key,
            s.score
        FROM scores s
        INNER JOIN players p ON s.player_key = p.player_key
        WHERE s.team_key = :team_key
            AND s.season = ANY(:seasons)
            AND s.machine_key = ANY(:machines)
            {roster_filter}
        ORDER BY s.player_key, s.machine_key, s.score
    """

    all_scores = execute_query(all_scores_query, query_params)

    # Group scores by player and machine
    player_machine_scores = defaultdict(lambda: defaultdict(list))
    player_names = {}

    for row in all_scores:
        player_key = row['player_key']
        player_names[player_key] = row['player_name']
        machine_key = row['machine_key']
        player_machine_scores[player_key][machine_key].append(row['score'])

    # Build confidence intervals
    result = []

    for player_key, machine_scores in player_machine_scores.items():
        player_name = player_names[player_key]

        for machine_key in available_machines:
            machine_name = machine_name_map.get(machine_key, machine_key)
            scores = machine_scores.get(machine_key, [])

            if len(scores) >= 5:
                ci = calculate_confidence_interval(scores)
                result.append(PlayerMachineConfidence(
                    player_key=player_key,
                    player_name=player_name,
                    machine_key=machine_key,
                    machine_name=machine_name,
                    confidence_interval=ci,
                    insufficient_data=False
                ))

    # Sort by sample size (most scores first)
    result.sort(key=lambda x: x.confidence_interval.sample_size if x.confidence_interval else 0, reverse=True)

    return result


def get_team_machine_confidence(
    team_key: str,
    available_machines: List[str],
    seasons: List[int]
) -> List[TeamMachineConfidence]:
    """
    Get confidence intervals for the team (all players combined) on each available machine across multiple seasons.
    OPTIMIZED: Single query to fetch all scores at once.
    """
    if not available_machines:
        return []

    # Get team name (from most recent season)
    team_query = "SELECT team_name FROM teams WHERE team_key = :team_key AND season = ANY(:seasons) ORDER BY season DESC LIMIT 1"
    team_result = execute_query(team_query, {'team_key': team_key, 'seasons': seasons})
    team_name = team_result[0]['team_name'] if team_result else team_key

    # Get all machine names in one query
    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    machine_names = execute_query(machine_names_query, {'machines': available_machines})
    machine_name_map = {m['machine_key']: m['machine_name'] for m in machine_names}

    # Get ALL scores for this team on all available machines in a single query
    all_scores_query = """
        SELECT machine_key, score
        FROM scores
        WHERE team_key = :team_key
            AND season = ANY(:seasons)
            AND machine_key = ANY(:machines)
        ORDER BY machine_key, score
    """

    all_scores = execute_query(all_scores_query, {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    })

    # Group scores by machine
    machine_scores = defaultdict(list)
    for row in all_scores:
        machine_scores[row['machine_key']].append(row['score'])

    # Build confidence intervals
    result = []
    for machine_key in available_machines:
        machine_name = machine_name_map.get(machine_key, machine_key)
        scores = machine_scores.get(machine_key, [])

        if len(scores) >= 5:
            ci = calculate_confidence_interval(scores)
            result.append(TeamMachineConfidence(
                team_key=team_key,
                team_name=team_name,
                machine_key=machine_key,
                machine_name=machine_name,
                confidence_interval=ci,
                insufficient_data=False
            ))

    # Sort by sample size (most scores first)
    result.sort(key=lambda x: x.confidence_interval.sample_size if x.confidence_interval else 0, reverse=True)

    return result


@router.get(
    "",
    response_model=MatchupAnalysis,
    responses={404: {"model": ErrorResponse}},
    summary="Analyze team matchup at a venue",
    description="Get comprehensive matchup analysis between two teams at a specific venue across one or more seasons"
)
def get_matchup_analysis(
    home_team: str = Query(..., description="Home team key (e.g., 'TRL')"),
    away_team: str = Query(..., description="Away team key (e.g., 'ETB')"),
    venue: str = Query(..., description="Venue key (e.g., 'T4B')"),
    seasons: Union[List[int], None] = Query(None, description="Season numbers (e.g., [21, 22])")
):
    """
    Analyze a matchup between two teams at a specific venue across one or more seasons.

    Returns:
    - Available machines at the venue
    - Team machine pick frequencies (aggregated across seasons)
    - Player machine preferences (aggregated across seasons)
    - Player-specific confidence intervals (aggregated across seasons)
    - Team-level confidence intervals (aggregated across seasons)

    Examples:
    - Single season: `/matchups?home_team=TRL&away_team=ETB&venue=T4B&seasons=22`
    - Multiple seasons: `/matchups?home_team=TRL&away_team=ETB&venue=T4B&seasons=21&seasons=22`

    Note: If no seasons specified, defaults to current season + previous season for better data coverage.
    """

    # Default to current season + previous season for better data coverage
    # This ensures we have enough historical data even for new seasons
    if not seasons or len(seasons) == 0:
        # Get the most recent season from the database
        latest_season_query = "SELECT MAX(season) as max_season FROM matches"
        latest_result = execute_query(latest_season_query, {})
        current_season = latest_result[0]['max_season'] if latest_result and latest_result[0]['max_season'] else 23
        seasons = [current_season, current_season - 1]

    # Validate teams exist in at least one season
    home_team_query = "SELECT team_name, home_venue_key, season FROM teams WHERE team_key = :team_key AND season = ANY(:seasons) ORDER BY season DESC LIMIT 1"
    home_team_result = execute_query(home_team_query, {'team_key': home_team, 'seasons': seasons})

    if not home_team_result:
        raise HTTPException(status_code=404, detail=f"Home team '{home_team}' not found in seasons {seasons}")

    home_team_name = home_team_result[0]['team_name']
    home_team_home_venue = home_team_result[0]['home_venue_key']

    away_team_result = execute_query(home_team_query, {'team_key': away_team, 'seasons': seasons})

    if not away_team_result:
        raise HTTPException(status_code=404, detail=f"Away team '{away_team}' not found in seasons {seasons}")

    away_team_name = away_team_result[0]['team_name']
    away_team_home_venue = away_team_result[0]['home_venue_key']

    # Validate venue exists
    venue_query = "SELECT venue_name FROM venues WHERE venue_key = :venue_key"
    venue_result = execute_query(venue_query, {'venue_key': venue})

    if not venue_result:
        raise HTTPException(status_code=404, detail=f"Venue '{venue}' not found")

    venue_name = venue_result[0]['venue_name']

    # Get available machines at venue
    available_machines = get_current_machines_for_venue(venue, seasons)

    if not available_machines:
        raise HTTPException(
            status_code=404,
            detail=f"No machine data found for venue '{venue}' in seasons {seasons}"
        )

    # Get team machine pick frequencies
    # Home team picks Round 4 - show only machines at this venue
    home_pick_freq = get_team_machine_pick_frequency(
        home_team, home_team_home_venue, available_machines, seasons, is_home_team_at_venue=True
    )
    # Away team picks Round 1 - show all their doubles picks across all venues
    away_pick_freq = get_team_machine_pick_frequency(
        away_team, away_team_home_venue, available_machines, seasons, is_home_team_at_venue=False
    )

    # Get player machine preferences - filtered to roster players only (is_substitute = false)
    home_player_prefs = get_player_machine_preferences(
        home_team, available_machines, seasons, roster_only=True
    )
    away_player_prefs = get_player_machine_preferences(
        away_team, available_machines, seasons, roster_only=True
    )

    # Get player confidence intervals - filtered to roster players only (is_substitute = false)
    home_player_confidence = get_player_machine_confidence(
        home_team, available_machines, seasons, roster_only=True
    )
    away_player_confidence = get_player_machine_confidence(
        away_team, available_machines, seasons, roster_only=True
    )

    # Get team confidence intervals
    home_team_confidence = get_team_machine_confidence(home_team, available_machines, seasons)
    away_team_confidence = get_team_machine_confidence(away_team, available_machines, seasons)

    # Format season display (single number or "21-22" for multiple)
    season_display = seasons[0] if len(seasons) == 1 else f"{min(seasons)}-{max(seasons)}"

    # Get full machine names for available machines
    machine_name_map = get_machine_names(available_machines)
    available_machines_info = [
        MachineInfo(key=key, name=machine_name_map.get(key, key))
        for key in available_machines
    ]
    # Sort by name alphabetically
    available_machines_info.sort(key=lambda m: m.name)

    return MatchupAnalysis(
        home_team_key=home_team,
        home_team_name=home_team_name,
        away_team_key=away_team,
        away_team_name=away_team_name,
        venue_key=venue,
        venue_name=venue_name,
        season=season_display,
        available_machines=available_machines,
        available_machines_info=available_machines_info,
        home_team_pick_frequency=home_pick_freq,
        away_team_pick_frequency=away_pick_freq,
        home_team_player_preferences=home_player_prefs,
        away_team_player_preferences=away_player_prefs,
        home_team_player_confidence=home_player_confidence,
        away_team_player_confidence=away_player_confidence,
        home_team_machine_confidence=home_team_confidence,
        away_team_machine_confidence=away_team_confidence
    )
