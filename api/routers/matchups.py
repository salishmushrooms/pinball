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
    seasons: List[int]
) -> List[MachinePickFrequency]:
    """
    Calculate how often a team picks each machine across multiple seasons.
    Counts with 2x multiplier for doubles rounds (1 & 4).
    Filtering logic:
    - At HOME venue: Team picks rounds 2 & 4
    - At AWAY venues: Team picks rounds 1 & 3
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
                    is_home_venue = (venue_key == team_home_venue)

                    # Determine which rounds this team picked
                    if is_home_venue:
                        team_pick_rounds = [2, 4]  # Home team picks rounds 2 & 4 at their venue
                    else:
                        # Away - need to check if this team is home or away in match
                        if team_key == home_team:
                            team_pick_rounds = [2, 4]  # Home in match picks 2 & 4
                        else:
                            team_pick_rounds = [1, 3]  # Away in match picks 1 & 3

                    # Process rounds
                    for round_data in match_data.get('rounds', []):
                        round_num = round_data.get('n')

                        for game in round_data.get('games', []):
                            machine = game.get('machine')

                            # Only count machines available at target venue
                            if machine not in available_machines:
                                continue

                            # Count picks (2x for doubles rounds 1 & 4)
                            if round_num in team_pick_rounds:
                                pick_multiplier = 2 if round_num in [1, 4] else 1
                                machine_picks[machine] += pick_multiplier

        # Build result
        result = []
        for machine_key in available_machines:
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
    seasons: List[int]
) -> List[PlayerMachinePreference]:
    """
    Get each player's machine picking preferences on this team across multiple seasons.
    OPTIMIZED: Single query to get all player machine counts.
    """
    if not available_machines:
        return []

    # Get all player-machine counts in a single query
    all_picks_query = """
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
        GROUP BY s.player_key, p.name, s.machine_key, m.machine_name
        ORDER BY s.player_key, times_played DESC
    """

    all_picks = execute_query(all_picks_query, {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    })

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
    seasons: List[int]
) -> List[PlayerMachineConfidence]:
    """
    Get confidence intervals for each player on each available machine across multiple seasons.
    OPTIMIZED: Single query to fetch all scores at once.
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

    # Get ALL scores for this team in a single query
    all_scores_query = """
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
        ORDER BY s.player_key, s.machine_key, s.score
    """

    all_scores = execute_query(all_scores_query, {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    })

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
    """

    # Default to season 22 if not specified
    if not seasons or len(seasons) == 0:
        seasons = [22]

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
    home_pick_freq = get_team_machine_pick_frequency(home_team, home_team_home_venue, available_machines, seasons)
    away_pick_freq = get_team_machine_pick_frequency(away_team, away_team_home_venue, available_machines, seasons)

    # Get player machine preferences
    home_player_prefs = get_player_machine_preferences(home_team, available_machines, seasons)
    away_player_prefs = get_player_machine_preferences(away_team, available_machines, seasons)

    # Get player confidence intervals
    home_player_confidence = get_player_machine_confidence(home_team, available_machines, seasons)
    away_player_confidence = get_player_machine_confidence(away_team, available_machines, seasons)

    # Get team confidence intervals
    home_team_confidence = get_team_machine_confidence(home_team, available_machines, seasons)
    away_team_confidence = get_team_machine_confidence(away_team, available_machines, seasons)

    # Format season display (single number or "21-22" for multiple)
    season_display = seasons[0] if len(seasons) == 1 else f"{min(seasons)}-{max(seasons)}"

    return MatchupAnalysis(
        home_team_key=home_team,
        home_team_name=home_team_name,
        away_team_key=away_team,
        away_team_name=away_team_name,
        venue_key=venue,
        venue_name=venue_name,
        season=season_display,
        available_machines=available_machines,
        home_team_pick_frequency=home_pick_freq,
        away_team_pick_frequency=away_pick_freq,
        home_team_player_preferences=home_player_prefs,
        away_team_player_preferences=away_player_prefs,
        home_team_player_confidence=home_player_confidence,
        away_team_player_confidence=away_player_confidence,
        home_team_machine_confidence=home_team_confidence,
        away_team_machine_confidence=away_team_confidence
    )
