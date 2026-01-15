"""
Predictions router for MNP Analyzer API

Provides endpoints for predicting machine picks, player lineups, and scores
based on historical data.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from collections import Counter
import logging
import json
import glob
from pathlib import Path

from etl.database import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"],
    responses={404: {"description": "Not found"}},
)


def get_venue_machines(venue_key: str, seasons: List[int]) -> List[str]:
    """
    Get the current machine lineup for a venue by checking the most recent match
    across multiple seasons (prioritizes higher season, then higher week).
    Returns list of machine keys that are currently at this venue.
    """
    most_recent_match = None
    highest_week = -1
    highest_season = -1

    try:
        # Check seasons in reverse order (most recent first)
        for season in sorted(seasons, reverse=True):
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
    except Exception as e:
        logger.warning(f"Could not get machines for venue {venue_key}: {e}")
        return []


@router.get("/machine-picks")
def predict_machine_picks(
    team_key: str = Query(..., description="Team making the pick (3-letter key)"),
    round_num: int = Query(..., ge=1, le=4, description="Round number (1-4)"),
    venue_key: str = Query(..., description="Venue where match is being played"),
    seasons: Optional[List[int]] = Query(
        default=[22, 23],
        description="Seasons to analyze for prediction (default: [22, 23])"
    ),
    limit: int = Query(default=10, ge=1, le=20, description="Number of predictions to return")
):
    """
    Predict which machines a team is likely to pick for a given round.

    ## Pick Rules
    - Home team picks machines in rounds 2 & 4
    - Away team picks machines in rounds 1 & 3

    ## Prediction Method (UPDATED for Doubles Rounds Only)
    For doubles rounds (1 & 4), analyzes ALL of the team's historical doubles picks:
    - Round 1 predictions (away team): Counts Round 1 picks (when away) + Round 4 picks (when home)
    - Round 4 predictions (home team): Counts Round 4 picks (when home) + Round 1 picks (when away)

    For singles rounds (2 & 3), uses the original logic matching the specific round context.

    ## Parameters
    - **team_key**: 3-letter team abbreviation (e.g., "SKP", "TRL", "ADB")
    - **round_num**: Round number (1, 2, 3, or 4)
    - **venue_key**: Venue code where match is played (e.g., "T4B", "KRA")
    - **seasons**: List of seasons to analyze (default: [21, 22])
    - **limit**: Number of top predictions to return (default: 10)

    ## Returns
    - **predictions**: List of machines with pick frequency and confidence
    - **sample_size**: Total number of historical picks analyzed
    - **context**: Description of the prediction context
    - **venue_machines**: Machines available at the venue (for filtering)
    """
    try:
        # Convert seasons to list of integers
        if not isinstance(seasons, list):
            seasons = [seasons]
        season_list = [int(s) for s in seasons]

        # Get venue machines - check across all seasons to find the most recent lineup
        venue_machines = get_venue_machines(venue_key, season_list)

        # Track machine picks across all seasons
        machine_picks = Counter()
        total_rounds = 0  # Track total number of rounds analyzed

        # Determine prediction strategy based on round
        is_doubles_round = round_num in [1, 4]

        if is_doubles_round:
            # NEW LOGIC: For doubles rounds, count ALL doubles picks
            context = "doubles (all home and away)"

            for season in season_list:
                matches_path = f"mnp-data-archive/season-{season}/matches"
                match_files = glob.glob(f"{matches_path}/*.json")

                for match_file in match_files:
                    try:
                        with open(match_file, 'r') as f:
                            match_data = json.load(f)

                        away_team = match_data.get('away', {}).get('key')
                        home_team = match_data.get('home', {}).get('key')

                        # Skip if team not in this match
                        if team_key not in [home_team, away_team]:
                            continue

                        is_team_home = (team_key == home_team)

                        # Process BOTH doubles rounds (1 & 4)
                        for round_data in match_data.get('rounds', []):
                            round_n = round_data.get('n')

                            # Only process doubles rounds
                            if round_n not in [1, 4]:
                                continue

                            # Determine if team picked this round
                            # Home team picks rounds 2 & 4, Away team picks rounds 1 & 3
                            team_picked_this_round = (
                                (is_team_home and round_n == 4) or
                                (not is_team_home and round_n == 1)
                            )

                            if team_picked_this_round:
                                total_rounds += 1
                                games = round_data.get('games', [])
                                if games:
                                    machine_key = games[0].get('machine')
                                    if machine_key:
                                        # Count ALL picks - filtering happens in frontend
                                        machine_picks[machine_key] += 1

                    except Exception as e:
                        logger.warning(f"Error processing match file {match_file}: {e}")
                        continue
        else:
            # SINGLES ROUNDS (2 & 3): Use original logic
            if round_num == 2:
                context = "home round 2"
            else:
                context = "away round 3"

            for season in season_list:
                matches_path = f"mnp-data-archive/season-{season}/matches"
                match_files = glob.glob(f"{matches_path}/*.json")

                for match_file in match_files:
                    try:
                        with open(match_file, 'r') as f:
                            match_data = json.load(f)

                        away_team = match_data.get('away', {}).get('key')
                        home_team = match_data.get('home', {}).get('key')

                        # Check if this team is playing in the right context
                        if round_num == 2 and home_team != team_key:
                            continue
                        if round_num == 3 and away_team != team_key:
                            continue

                        # Get machines from the specific round
                        for round_data in match_data.get('rounds', []):
                            if round_data.get('n') == round_num:
                                total_rounds += 1
                                games = round_data.get('games', [])
                                if games:
                                    machine_key = games[0].get('machine')
                                    if machine_key:
                                        machine_picks[machine_key] += 1
                                break

                    except Exception as e:
                        logger.warning(f"Error processing match file {match_file}: {e}")
                        continue

        # Calculate total picks (should equal total_rounds)
        total_picks = sum(machine_picks.values())

        if total_picks == 0:
            return {
                "predictions": [],
                "sample_size": 0,
                "total_rounds": total_rounds,
                "context": f"{context} round {round_num}",
                "venue_machines": venue_machines,
                "team_key": team_key,
                "venue_key": venue_key,
                "seasons_analyzed": season_list,
                "message": f"No historical data found for {team_key} in {context} round {round_num}"
            }

        # Load machine names from machine_variations.json
        machine_names = {}
        try:
            with open("machine_variations.json", 'r') as f:
                machine_variations = json.load(f)
                for machine_key in machine_picks.keys():
                    if machine_key in machine_variations:
                        machine_names[machine_key] = machine_variations[machine_key].get('name', machine_key)
                    else:
                        machine_names[machine_key] = machine_key
        except Exception as e:
            logger.warning(f"Could not load machine names: {e}")
            machine_names = {k: k for k in machine_picks.keys()}

        # Build predictions
        predictions = []
        for machine_key, count in machine_picks.most_common(limit):
            confidence = (count / total_picks) * 100
            available_at_venue = machine_key in venue_machines

            predictions.append({
                "machine_key": machine_key,
                "machine_name": machine_names.get(machine_key, machine_key),
                "pick_count": count,
                "confidence_pct": round(confidence, 1),
                "available_at_venue": available_at_venue
            })

        return {
            "predictions": predictions,
            "sample_size": total_picks,
            "total_rounds": total_rounds,
            "context": f"{context} round {round_num}",
            "team_key": team_key,
            "venue_key": venue_key,
            "venue_machines": venue_machines,
            "seasons_analyzed": season_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting machine picks: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to predict machine picks: {str(e)}"
        )
