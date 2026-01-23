"""
Matchup calculation service - shared logic for API and ETL.

This module contains the core matchup calculation functions that can be
used by both the API endpoint (on-demand) and ETL script (batch pre-calculation).
"""

from typing import Optional, List, Dict, Any
from collections import defaultdict
import json
import math

from api.models.schemas import (
    MatchupAnalysis,
    MachinePickFrequency,
    PlayerMachinePreference,
    PlayerMachineConfidence,
    TeamMachineConfidence,
    ConfidenceInterval,
    MachineInfo,
)
from api.dependencies import execute_query


def get_current_machines_for_venue(venue_key: str, seasons: List[int]) -> List[str]:
    """
    Get the machine lineup for a venue from the database.
    Returns list of machine keys that are active at this venue for the most recent season requested.
    """
    try:
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

    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    results = execute_query(machine_names_query, {'machines': machine_keys})
    name_map = {m['machine_key']: m['machine_name'] for m in results}

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


def calculate_confidence_interval(
    scores: List[float],
    confidence_level: float = 95.0
) -> Optional[ConfidenceInterval]:
    """
    Calculate confidence interval for a list of scores.
    Returns None if insufficient data (< 5 scores).
    """
    if len(scores) < 5:
        return None

    mean = sum(scores) / len(scores)
    variance = sum((x - mean) ** 2 for x in scores) / len(scores)
    std_dev = math.sqrt(variance)

    z_score = 1.96 if confidence_level == 95.0 else 1.645

    margin_of_error = z_score * (std_dev / math.sqrt(len(scores)))

    return ConfidenceInterval(
        mean=mean,
        std_dev=std_dev,
        lower_bound=max(0, mean - margin_of_error),
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

    Returns pick rate (times_picked / total_opportunities) for each machine,
    sorted by Wilson score for confidence-weighted ranking.
    """
    try:
        if not available_machines:
            return []

        # Query includes total_opportunities and wilson_lower for proper pick rate calculation
        # Filter by minimum 3 opportunities to exclude unreliable data
        query = """
            SELECT
                tmp.machine_key,
                m.machine_name,
                SUM(tmp.times_picked) as total_picked,
                SUM(tmp.total_opportunities) as total_opportunities,
                MAX(tmp.wilson_lower) as wilson_lower
            FROM team_machine_picks tmp
            INNER JOIN machines m ON tmp.machine_key = m.machine_key
            WHERE tmp.team_key = :team_key
            AND tmp.season = ANY(:seasons)
            AND tmp.round_type = 'doubles'
            AND tmp.machine_key = ANY(:machines)
            GROUP BY tmp.machine_key, m.machine_name
            HAVING SUM(tmp.total_opportunities) >= 3
            ORDER BY wilson_lower DESC
        """

        results = execute_query(query, {
            'team_key': team_key,
            'seasons': seasons,
            'machines': available_machines
        })

        result = []
        for row in results:
            times_picked = row['total_picked']
            total_opportunities = row['total_opportunities'] or 0

            # Calculate pick percentage as pick rate (picks / opportunities)
            # Capped at 100% to handle data inconsistencies where picks > opportunities
            pick_percentage = 0.0
            if total_opportunities > 0:
                pick_percentage = round(min((times_picked / total_opportunities) * 100, 100.0), 1)

            result.append(MachinePickFrequency(
                machine_key=row['machine_key'],
                machine_name=row['machine_name'],
                times_picked=times_picked,
                total_opportunities=total_opportunities,
                pick_percentage=pick_percentage
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
    """
    if not available_machines:
        return []

    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_only:
        roster_filter = "AND s.is_substitute = false"

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

    player_picks = defaultdict(list)
    for pick in all_picks:
        player_key = pick['player_key']
        player_picks[player_key].append({
            'player_name': pick['player_name'],
            'machine_key': pick['machine_key'],
            'machine_name': pick['machine_name'],
            'times_played': pick['times_played']
        })

    result = []
    for player_key, picks in player_picks.items():
        if picks:
            player_name = picks[0]['player_name']
            top_machines = [
                MachinePickFrequency(
                    machine_key=pick['machine_key'],
                    machine_name=pick['machine_name'],
                    times_picked=pick['times_played'],
                    total_opportunities=pick['times_played'],
                    pick_percentage=100.0
                )
                for pick in picks[:5]
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
    """
    if not available_machines:
        return []

    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    machine_names = execute_query(machine_names_query, {'machines': available_machines})
    machine_name_map = {m['machine_key']: m['machine_name'] for m in machine_names}

    query_params = {
        'team_key': team_key,
        'seasons': seasons,
        'machines': available_machines
    }

    roster_filter = ""
    if roster_only:
        roster_filter = "AND s.is_substitute = false"

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

    player_machine_scores = defaultdict(lambda: defaultdict(list))
    player_names = {}

    for row in all_scores:
        player_key = row['player_key']
        player_names[player_key] = row['player_name']
        machine_key = row['machine_key']
        player_machine_scores[player_key][machine_key].append(row['score'])

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

    result.sort(
        key=lambda x: x.confidence_interval.sample_size if x.confidence_interval else 0,
        reverse=True
    )

    return result


def get_team_machine_confidence(
    team_key: str,
    available_machines: List[str],
    seasons: List[int]
) -> List[TeamMachineConfidence]:
    """
    Get confidence intervals for the team (all players combined) on each available machine.
    """
    if not available_machines:
        return []

    team_query = """
        SELECT team_name FROM teams
        WHERE team_key = :team_key AND season = ANY(:seasons)
        ORDER BY season DESC LIMIT 1
    """
    team_result = execute_query(team_query, {'team_key': team_key, 'seasons': seasons})
    team_name = team_result[0]['team_name'] if team_result else team_key

    machine_names_query = """
        SELECT machine_key, machine_name
        FROM machines
        WHERE machine_key = ANY(:machines)
    """
    machine_names = execute_query(machine_names_query, {'machines': available_machines})
    machine_name_map = {m['machine_key']: m['machine_name'] for m in machine_names}

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

    machine_scores = defaultdict(list)
    for row in all_scores:
        machine_scores[row['machine_key']].append(row['score'])

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

    result.sort(
        key=lambda x: x.confidence_interval.sample_size if x.confidence_interval else 0,
        reverse=True
    )

    return result


def calculate_full_matchup_analysis(
    home_team: str,
    away_team: str,
    venue: str,
    seasons: List[int]
) -> Optional[Dict[str, Any]]:
    """
    Calculate complete matchup analysis.

    Returns dict suitable for JSON storage or API response.
    Returns None if insufficient data (e.g., no machines at venue).
    """
    # Validate teams exist
    team_query = """
        SELECT team_name, home_venue_key
        FROM teams
        WHERE team_key = :team_key AND season = ANY(:seasons)
        ORDER BY season DESC LIMIT 1
    """

    home_team_result = execute_query(team_query, {'team_key': home_team, 'seasons': seasons})
    if not home_team_result:
        return None

    home_team_name = home_team_result[0]['team_name']
    home_team_home_venue = home_team_result[0]['home_venue_key']

    away_team_result = execute_query(team_query, {'team_key': away_team, 'seasons': seasons})
    if not away_team_result:
        return None

    away_team_name = away_team_result[0]['team_name']
    away_team_home_venue = away_team_result[0]['home_venue_key']

    # Get venue name
    venue_query = "SELECT venue_name FROM venues WHERE venue_key = :venue_key"
    venue_result = execute_query(venue_query, {'venue_key': venue})
    if not venue_result:
        return None

    venue_name = venue_result[0]['venue_name']

    # Get available machines
    available_machines = get_current_machines_for_venue(venue, seasons)
    if not available_machines:
        return None

    # Calculate all components
    home_pick_freq = get_team_machine_pick_frequency(
        home_team, home_team_home_venue, available_machines, seasons, True
    )
    away_pick_freq = get_team_machine_pick_frequency(
        away_team, away_team_home_venue, available_machines, seasons, False
    )

    home_player_prefs = get_player_machine_preferences(home_team, available_machines, seasons, True)
    away_player_prefs = get_player_machine_preferences(away_team, available_machines, seasons, True)

    home_player_confidence = get_player_machine_confidence(home_team, available_machines, seasons, True)
    away_player_confidence = get_player_machine_confidence(away_team, available_machines, seasons, True)

    home_team_confidence = get_team_machine_confidence(home_team, available_machines, seasons)
    away_team_confidence = get_team_machine_confidence(away_team, available_machines, seasons)

    # Format season display
    season_display = str(seasons[0]) if len(seasons) == 1 else f"{min(seasons)}-{max(seasons)}"

    # Get machine names
    machine_name_map = get_machine_names(available_machines)
    available_machines_info = [
        MachineInfo(key=key, name=machine_name_map.get(key, key))
        for key in available_machines
    ]
    available_machines_info.sort(key=lambda m: m.name)

    # Build MatchupAnalysis object
    analysis = MatchupAnalysis(
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

    # Convert to dict for JSONB storage
    return analysis.model_dump()
