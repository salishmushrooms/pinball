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
    limit: int = Query(default=10, ge=1, le=20, description="Number of predictions to return"),
    min_opportunities: int = Query(default=3, ge=1, le=10, description="Minimum opportunities required")
):
    """
    Predict which machines a team is likely to pick for a given round.

    ## Pick Rules
    - Home team picks machines in rounds 2 & 4
    - Away team picks machines in rounds 1 & 3

    ## Prediction Method
    Calculates **pick rate** (picks / opportunities) where opportunities are matches
    where the machine was available at the venue. Uses Wilson score for confidence-
    weighted ranking so small samples don't dominate (1/1 won't beat 7/10).

    ## Parameters
    - **team_key**: 3-letter team abbreviation (e.g., "SKP", "TRL", "ADB")
    - **round_num**: Round number (1, 2, 3, or 4)
    - **venue_key**: Venue code where match is played (e.g., "T4B", "KRA")
    - **seasons**: List of seasons to analyze (default: [22, 23])
    - **limit**: Number of top predictions to return (default: 10)
    - **min_opportunities**: Minimum opportunities required to show (default: 3)

    ## Returns
    - **predictions**: List of machines with pick rate, opportunities, and confidence
    - **sample_size**: Total number of pick opportunities
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

        # Determine round type
        # Rounds 1 & 4 are doubles, Rounds 2 & 3 are singles
        # We combine home AND away pick data to get a complete picture of
        # the team's machine preferences (e.g., if they love Medieval Madness,
        # they'll pick it both at home and when visiting venues that have it)
        is_doubles_round = round_num in [1, 4]
        round_type = 'doubles' if is_doubles_round else 'singles'
        context = round_type

        # Query team_machine_picks table combining home and away picks
        # This gives us the team's overall preference for each machine
        # Opportunities = home opportunities + away opportunities (when machine was available)
        query = """
            SELECT
                tmp.machine_key,
                m.machine_name,
                SUM(tmp.times_picked) as pick_count,
                SUM(tmp.total_opportunities) as opportunities,
                MAX(tmp.wilson_lower) as wilson_lower
            FROM team_machine_picks tmp
            INNER JOIN machines m ON tmp.machine_key = m.machine_key
            WHERE tmp.team_key = :team_key
            AND tmp.season = ANY(:seasons)
            AND tmp.round_type = :round_type
            GROUP BY tmp.machine_key, m.machine_name
            HAVING SUM(tmp.total_opportunities) >= :min_opportunities
            ORDER BY wilson_lower DESC
            LIMIT :limit
        """

        results = execute_query(query, {
            'team_key': team_key,
            'seasons': season_list,
            'round_type': round_type,
            'min_opportunities': min_opportunities,
            'limit': limit
        })

        # Calculate actual pick rounds (max opportunities for any single machine)
        # This represents the true number of times the team had a pick in this round type
        # (summing across machines would give a meaninglessly large number)
        actual_pick_rounds = max(row['opportunities'] for row in results) if results else 0

        if not results:
            return {
                "predictions": [],
                "sample_size": 0,
                "total_rounds": 0,
                "context": context,
                "venue_machines": venue_machines,
                "team_key": team_key,
                "venue_key": venue_key,
                "seasons_analyzed": season_list,
                "message": f"No historical data found for {team_key} in {context} round {round_num}"
            }

        # Build predictions with pick rate (picks/opportunities)
        predictions = []
        for row in results:
            pick_count = row['pick_count']
            opportunities = row['opportunities']
            wilson_lower = row['wilson_lower'] or 0

            # Calculate pick rate as percentage (capped at 100% for data inconsistencies)
            pick_rate_pct = min((pick_count / opportunities * 100), 100.0) if opportunities > 0 else 0
            available_at_venue = row['machine_key'] in venue_machines

            predictions.append({
                "machine_key": row['machine_key'],
                "machine_name": row['machine_name'],
                "pick_count": pick_count,
                "opportunities": opportunities,
                "confidence_pct": round(pick_rate_pct, 1),  # Keep name for backward compat
                "confidence_score": round(wilson_lower * 100, 1),  # Wilson score as 0-100
                "available_at_venue": available_at_venue
            })

        return {
            "predictions": predictions,
            "sample_size": actual_pick_rounds,
            "total_rounds": actual_pick_rounds,
            "context": context,
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
