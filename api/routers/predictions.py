"""
Predictions router for MNP Analyzer API

Provides endpoints for predicting machine picks, player lineups, and scores
based on historical data.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

from api.dependencies import execute_query

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/predictions",
    tags=["predictions"],
    responses={404: {"description": "Not found"}},
)


def get_venue_machines(venue_key: str, seasons: List[int]) -> List[str]:
    """
    Get the current machine lineup for a venue from the database.
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

        # Get venue machines from database
        venue_machines = get_venue_machines(venue_key, season_list)

        # Determine prediction strategy based on round
        is_doubles_round = round_num in [1, 4]

        if is_doubles_round:
            # For doubles rounds, query team_machine_picks for doubles picks
            context = "doubles (all home and away)"
            round_type = 'doubles'
        else:
            # For singles rounds
            if round_num == 2:
                context = "home round 2"
            else:
                context = "away round 3"
            round_type = 'singles'

        # Query team_machine_picks table for pick data
        query = """
            SELECT
                tmp.machine_key,
                m.machine_name,
                SUM(tmp.times_picked) as pick_count
            FROM team_machine_picks tmp
            INNER JOIN machines m ON tmp.machine_key = m.machine_key
            WHERE tmp.team_key = :team_key
            AND tmp.season = ANY(:seasons)
            AND tmp.round_type = :round_type
            GROUP BY tmp.machine_key, m.machine_name
            ORDER BY pick_count DESC
            LIMIT :limit
        """

        results = execute_query(query, {
            'team_key': team_key,
            'seasons': season_list,
            'round_type': round_type,
            'limit': limit
        })

        # Calculate total picks
        total_picks = sum(row['pick_count'] for row in results)

        if total_picks == 0:
            return {
                "predictions": [],
                "sample_size": 0,
                "total_rounds": 0,
                "context": f"{context} round {round_num}",
                "venue_machines": venue_machines,
                "team_key": team_key,
                "venue_key": venue_key,
                "seasons_analyzed": season_list,
                "message": f"No historical data found for {team_key} in {context} round {round_num}"
            }

        # Build predictions
        predictions = []
        for row in results:
            confidence = (row['pick_count'] / total_picks) * 100
            available_at_venue = row['machine_key'] in venue_machines

            predictions.append({
                "machine_key": row['machine_key'],
                "machine_name": row['machine_name'],
                "pick_count": row['pick_count'],
                "confidence_pct": round(confidence, 1),
                "available_at_venue": available_at_venue
            })

        return {
            "predictions": predictions,
            "sample_size": total_picks,
            "total_rounds": total_picks,  # Approximation since we're using aggregated data
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
