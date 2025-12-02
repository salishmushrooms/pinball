"""
Seasons Router

Endpoints for fetching season schedule data from season.json files.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/seasons",
    tags=["seasons"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{season}/schedule")
def get_season_schedule(season: int):
    """
    Get the complete schedule for a specific season from season.json

    Returns all weeks and matches for the season, including team schedules.
    """
    try:
        season_file = f"mnp-data-archive/season-{season}/season.json"

        if not os.path.exists(season_file):
            raise HTTPException(
                status_code=404,
                detail=f"Season {season} schedule not found"
            )

        with open(season_file, 'r') as f:
            season_data = json.load(f)

        return season_data

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Season {season} schedule not found"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in season {season} file"
        )
    except Exception as e:
        logger.error(f"Error fetching season {season} schedule: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch season schedule"
        )


@router.get("/{season}/matches")
def get_season_matches(
    season: int,
    week: Optional[int] = Query(None, description="Filter by week number")
):
    """
    Get all matches for a season, optionally filtered by week

    Returns a flat list of matches with home/away teams and venue information.
    """
    try:
        season_file = f"mnp-data-archive/season-{season}/season.json"

        if not os.path.exists(season_file):
            raise HTTPException(
                status_code=404,
                detail=f"Season {season} not found"
            )

        with open(season_file, 'r') as f:
            season_data = json.load(f)

        # Flatten all matches from all weeks
        all_matches = []
        for week_data in season_data.get('weeks', []):
            week_num = week_data.get('n')

            # Filter by week if specified
            if week is not None and str(week_num) != str(week):
                continue

            for match in week_data.get('matches', []):
                match_info = {
                    **match,
                    'week': week_num,
                    'week_label': week_data.get('label'),
                    'date': week_data.get('date'),
                    'is_playoffs': week_data.get('isPlayoffs', False)
                }
                all_matches.append(match_info)

        return {
            "season": season,
            "week": week,
            "matches": all_matches,
            "count": len(all_matches)
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Season {season} not found"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in season {season} file"
        )
    except Exception as e:
        logger.error(f"Error fetching season {season} matches: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch season matches"
        )


@router.get("/{season}/teams/{team_key}/schedule")
def get_team_schedule(season: int, team_key: str):
    """
    Get the schedule for a specific team in a season

    Returns the team's complete schedule including home and away games.
    """
    try:
        season_file = f"mnp-data-archive/season-{season}/season.json"

        if not os.path.exists(season_file):
            raise HTTPException(
                status_code=404,
                detail=f"Season {season} not found"
            )

        with open(season_file, 'r') as f:
            season_data = json.load(f)

        # Find the team in the teams object
        team_data = season_data.get('teams', {}).get(team_key.upper())

        if not team_data:
            raise HTTPException(
                status_code=404,
                detail=f"Team {team_key} not found in season {season}"
            )

        return {
            "season": season,
            "team_key": team_key.upper(),
            "team_name": team_data.get('name'),
            "home_venue": team_data.get('venue'),
            "schedule": team_data.get('schedule', []),
            "roster": team_data.get('roster', [])
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Season {season} not found"
        )
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in season {season} file"
        )
    except Exception as e:
        logger.error(f"Error fetching team {team_key} schedule for season {season}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch team schedule"
        )
