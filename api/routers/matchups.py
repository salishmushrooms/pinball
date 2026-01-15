"""
Matchup API endpoints for analyzing team vs team matchups
"""
from typing import Optional, List, Dict, Union
from fastapi import APIRouter, HTTPException, Query
import json
import glob
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
    Get the machine lineup for a venue by checking the most recent match across seasons.
    Returns list of machine keys that are at this venue.
    """
    most_recent_match = None
    highest_week = -1
    highest_season = -1

    try:
        for season in seasons:
            matches_path = f"mnp-data-archive/season-{season}/matches"
            match_files = glob.glob(f"{matches_path}/*.json")

            for match_file in match_files:
                with open(match_file, 'r') as f:
                    match_data = json.load(f)
                    if match_data.get('venue', {}).get('key') == venue_key:
                        week = int(match_data.get('week', 0))
                        # Prioritize higher season, then higher week
                        if (season > highest_season) or (season == highest_season and week > highest_week):
                            highest_season = season
                            highest_week = week
                            most_recent_match = match_data

        if most_recent_match and 'venue' in most_recent_match and 'machines' in most_recent_match['venue']:
            return most_recent_match['venue']['machines']

        return []
    except Exception:
        return []


def get_team_roster(team_key: str, season: int) -> List[str]:
    """
    Get the roster player keys for a team in a specific season.
    Returns list of player_key strings from season.json roster.
    """
    try:
        season_file = f"mnp-data-archive/season-{season}/season.json"
        with open(season_file, 'r') as f:
            season_data = json.load(f)

        team_data = season_data.get('teams', {}).get(team_key.upper())
        if not team_data:
            return []

        roster = team_data.get('roster', [])
        # Roster entries are player keys (strings)
        return [p for p in roster if isinstance(p, str)]
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
    Counts with 2x multiplier for doubles rounds (1 & 4).

    Strategy:
    - Counts ALL of the team's doubles picks (Round 1 when away + Round 4 when home)
      across ALL venues to get comprehensive historical data
    - Filters results to only show machines in available_machines (at target venue)
    - This provides better predictions by using more data while keeping results relevant

    The is_home_team_at_venue parameter is kept for compatibility but both home
    and away teams now use the same logic.
    """
    machine_picks = defaultdict(int)

    try:
        for season in seasons:
            matches_path = f"mnp-data-archive/season-{season}/matches"
            match_files = glob.glob(f"{matches_path}/*.json")

            for match_file in match_files:
                with open(match_file, 'r') as f:
                    match_data = json.load(f)

                    # Only process matches involving this team
                    home_team = match_data.get('home', {}).get('key')
                    away_team = match_data.get('away', {}).get('key')

                    if team_key not in [home_team, away_team]:
                        continue

                    venue_key = match_data.get('venue', {}).get('key')
                    is_team_home_in_match = (team_key == home_team)
                    is_at_team_home_venue = (venue_key == team_home_venue)

                    # Determine which DOUBLES rounds (1 & 4 only) this team picked
                    # When team is home in match: picks rounds 2 & 4
                    # When team is away in match: picks rounds 1 & 3
                    if is_team_home_in_match:
                        # Team is home - they pick round 4 (doubles)
                        team_doubles_pick_rounds = [4]
                    else:
                        # Team is away - they pick round 1 (doubles)
                        team_doubles_pick_rounds = [1]

                    # Process rounds - only doubles rounds (1 & 4)
                    for round_data in match_data.get('rounds', []):
                        round_num = round_data.get('n')

                        # Only process doubles rounds
                        if round_num not in [1, 4]:
                            continue

                        for game in round_data.get('games', []):
                            machine = game.get('machine')

                            # Count picks only if this team picked this doubles round
                            if round_num in team_doubles_pick_rounds:
                                # Count ALL picks (2x multiplier for doubles rounds)
                                # Filtering to venue machines happens when building results
                                machine_picks[machine] += 2

        # Build result
        result = []

        # Always filter to only show machines available at the venue
        # This gives relevant predictions based on comprehensive historical data
        machines_to_show = available_machines

        for machine_key in machines_to_show:
            times_picked = machine_picks.get(machine_key, 0)

            if times_picked > 0:
                # Get machine name
                machine_name_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
                machine_result = execute_query(machine_name_query, {'machine_key': machine_key})
                machine_name = machine_result[0]['machine_name'] if machine_result else machine_key

                result.append(MachinePickFrequency(
                    machine_key=machine_key,
                    machine_name=machine_name,
                    times_picked=times_picked,
                    total_opportunities=0,  # Deprecated field
                    pick_percentage=0.0  # Deprecated field
                ))

        # Sort by times_picked descending
        result.sort(key=lambda x: x.times_picked, reverse=True)
        return result

    except Exception as e:
        print(f"Error calculating pick frequency: {e}")
        return []


def get_player_machine_preferences(
    team_key: str,
    available_machines: List[str],
    seasons: List[int],
    roster_players: Optional[List[str]] = None
) -> List[PlayerMachinePreference]:
    """
    Get each player's machine picking preferences on this team across multiple seasons.
    OPTIMIZED: Single query to get all player machine counts.

    Args:
        roster_players: If provided, only include these player keys in results
    """
    if not available_machines:
        return []

    # Build the query with optional roster filtering
    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_players:
        roster_filter = "AND s.player_key = ANY(:roster_players)"
        query_params['roster_players'] = roster_players

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
    roster_players: Optional[List[str]] = None
) -> List[PlayerMachineConfidence]:
    """
    Get confidence intervals for each player on each available machine across multiple seasons.
    OPTIMIZED: Single query to fetch all scores at once.

    Args:
        roster_players: If provided, only include these player keys in results
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

    # Build query with optional roster filtering
    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_players:
        roster_filter = "AND s.player_key = ANY(:roster_players)"
        query_params['roster_players'] = roster_players

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

    # Get current roster for each team (use highest season for current roster)
    current_season = max(seasons)
    home_roster = get_team_roster(home_team, current_season)
    away_roster = get_team_roster(away_team, current_season)

    # Get team machine pick frequencies
    # Home team picks Round 4 - show only machines at this venue
    home_pick_freq = get_team_machine_pick_frequency(
        home_team, home_team_home_venue, available_machines, seasons, is_home_team_at_venue=True
    )
    # Away team picks Round 1 - show all their doubles picks across all venues
    away_pick_freq = get_team_machine_pick_frequency(
        away_team, away_team_home_venue, available_machines, seasons, is_home_team_at_venue=False
    )

    # Get player machine preferences - filtered to current roster only
    home_player_prefs = get_player_machine_preferences(
        home_team, available_machines, seasons,
        roster_players=home_roster if home_roster else None
    )
    away_player_prefs = get_player_machine_preferences(
        away_team, available_machines, seasons,
        roster_players=away_roster if away_roster else None
    )

    # Get player confidence intervals - filtered to current roster only
    home_player_confidence = get_player_machine_confidence(
        home_team, available_machines, seasons,
        roster_players=home_roster if home_roster else None
    )
    away_player_confidence = get_player_machine_confidence(
        away_team, available_machines, seasons,
        roster_players=away_roster if away_roster else None
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
