"""
Matchup API endpoints for analyzing team vs team matchups
"""
from typing import Optional, List, Union
from fastapi import APIRouter, HTTPException, Query

from api.models.schemas import (
    MatchupAnalysis,
    MachineInfo,
    ErrorResponse
)
from api.dependencies import execute_query
from api.services.matchup_calculator import (
    get_current_machines_for_venue,
    get_machine_names,
    get_team_machine_pick_frequency,
    get_player_machine_preferences,
    get_player_machine_confidence,
    get_team_machine_confidence,
    calculate_full_matchup_analysis,
)

router = APIRouter(prefix="/matchups", tags=["matchups"])


@router.get(
    "/precomputed/{match_key}",
    response_model=MatchupAnalysis,
    responses={404: {"model": ErrorResponse}},
    summary="Get pre-computed matchup analysis",
    description="Returns pre-computed matchup analysis for a scheduled match. Much faster than on-demand calculation."
)
def get_precomputed_matchup(match_key: str):
    """
    Get pre-computed matchup analysis for a specific match.

    This endpoint serves static pre-calculated data that is refreshed weekly.
    Falls back to on-demand calculation if pre-computed data is not available.
    """
    # Try to get pre-computed data
    query = """
        SELECT analysis_data, last_calculated
        FROM pre_calculated_matchups
        WHERE match_key = :match_key
    """
    results = execute_query(query, {'match_key': match_key})

    if results and results[0]['analysis_data']:
        # Return pre-computed data directly
        return results[0]['analysis_data']

    # Fallback: Get match details and calculate on-demand
    match_query = """
        SELECT
            m.home_team_key, m.away_team_key, m.venue_key, m.season
        FROM matches m
        WHERE m.match_key = :match_key
    """
    match_results = execute_query(match_query, {'match_key': match_key})

    if not match_results:
        raise HTTPException(status_code=404, detail=f"Match '{match_key}' not found")

    match = match_results[0]
    seasons = [match['season'], match['season'] - 1]

    # Calculate on-demand using the service
    analysis = calculate_full_matchup_analysis(
        home_team=match['home_team_key'],
        away_team=match['away_team_key'],
        venue=match['venue_key'],
        seasons=seasons
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"Insufficient data to analyze match '{match_key}'"
        )

    return analysis


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
    if not seasons or len(seasons) == 0:
        latest_season_query = "SELECT MAX(season) as max_season FROM matches"
        latest_result = execute_query(latest_season_query, {})
        current_season = latest_result[0]['max_season'] if latest_result and latest_result[0]['max_season'] else 23
        seasons = [current_season, current_season - 1]

    # Validate teams exist in at least one season
    team_query = """
        SELECT team_name, home_venue_key, season
        FROM teams
        WHERE team_key = :team_key AND season = ANY(:seasons)
        ORDER BY season DESC LIMIT 1
    """
    home_team_result = execute_query(team_query, {'team_key': home_team, 'seasons': seasons})

    if not home_team_result:
        raise HTTPException(status_code=404, detail=f"Home team '{home_team}' not found in seasons {seasons}")

    home_team_name = home_team_result[0]['team_name']
    home_team_home_venue = home_team_result[0]['home_venue_key']

    away_team_result = execute_query(team_query, {'team_key': away_team, 'seasons': seasons})

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
    home_pick_freq = get_team_machine_pick_frequency(
        home_team, home_team_home_venue, available_machines, seasons, is_home_team_at_venue=True
    )
    away_pick_freq = get_team_machine_pick_frequency(
        away_team, away_team_home_venue, available_machines, seasons, is_home_team_at_venue=False
    )

    # Get player machine preferences - filtered to roster players only
    home_player_prefs = get_player_machine_preferences(
        home_team, available_machines, seasons, roster_only=True
    )
    away_player_prefs = get_player_machine_preferences(
        away_team, available_machines, seasons, roster_only=True
    )

    # Get player confidence intervals - filtered to roster players only
    home_player_confidence = get_player_machine_confidence(
        home_team, available_machines, seasons, roster_only=True
    )
    away_player_confidence = get_player_machine_confidence(
        away_team, available_machines, seasons, roster_only=True
    )

    # Get team confidence intervals
    home_team_confidence = get_team_machine_confidence(home_team, available_machines, seasons)
    away_team_confidence = get_team_machine_confidence(away_team, available_machines, seasons)

    # Format season display
    season_display = seasons[0] if len(seasons) == 1 else f"{min(seasons)}-{max(seasons)}"

    # Get full machine names for available machines
    machine_name_map = get_machine_names(available_machines)
    available_machines_info = [
        MachineInfo(key=key, name=machine_name_map.get(key, key))
        for key in available_machines
    ]
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
