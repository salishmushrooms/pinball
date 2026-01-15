"""
Seasons Router

Endpoints for fetching season schedule data from the database.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from api.dependencies import execute_query

logger = logging.getLogger(__name__)


def parse_season_date(date_str: str) -> Optional[datetime]:
    """
    Parse date from season.json format (MM/DD/YYYY or YYYYMMDD).
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    try:
        # Try MM/DD/YYYY format first
        if '/' in date_str:
            return datetime.strptime(date_str, "%m/%d/%Y")
        # Try YYYYMMDD format
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return None

router = APIRouter(
    prefix="/seasons",
    tags=["seasons"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{season}/status")
def get_season_status(season: int):
    """
    Get the status of a specific season.

    Returns whether the season is upcoming, in-progress, or completed,
    along with relevant dates and match counts.
    Queries from database (works in production without filesystem access).
    """
    try:
        # Get season date range and match counts from database
        query = """
            SELECT
                MIN(date) as first_date,
                MAX(date) as last_date,
                COUNT(*) as total_matches,
                SUM(CASE WHEN state = 'scheduled' THEN 1 ELSE 0 END) as scheduled_matches,
                SUM(CASE WHEN state = 'complete' THEN 1 ELSE 0 END) as completed_matches,
                SUM(CASE WHEN date >= CURRENT_DATE THEN 1 ELSE 0 END) as upcoming_matches
            FROM matches
            WHERE season = :season
        """
        results = execute_query(query, {"season": season})

        if not results or results[0]['total_matches'] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Season {season} not found"
            )

        row = results[0]
        first_week_date = row['first_date']
        last_week_date = row['last_date']
        total_matches = row['total_matches']
        upcoming_matches = row['upcoming_matches'] or 0
        completed_matches = row['completed_matches'] or 0

        now = datetime.now()

        # Determine season status
        if first_week_date is None:
            status = "unknown"
            message = "Unable to determine season dates"
        elif now.date() < first_week_date:
            status = "upcoming"
            message = f"Season {season} starts on {first_week_date.strftime('%B %d, %Y')}"
        elif completed_matches == total_matches:
            status = "completed"
            message = f"Season {season} has completed. Check back for Season {season + 1}!"
        elif now.date() <= last_week_date + timedelta(days=1):
            status = "in_progress"
            message = f"Season {season} is currently in progress with {upcoming_matches} upcoming matches"
        else:
            status = "completed"
            message = f"Season {season} has completed. Check back for Season {season + 1}!"

        return {
            "season": season,
            "status": status,
            "message": message,
            "first_week_date": first_week_date.strftime("%Y-%m-%d") if first_week_date else None,
            "last_week_date": last_week_date.strftime("%Y-%m-%d") if last_week_date else None,
            "total_matches": total_matches,
            "upcoming_matches": upcoming_matches
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching season {season} status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch season status"
        )


@router.get("/{season}/schedule")
def get_season_schedule(season: int):
    """
    Get the complete schedule for a specific season from the database.

    Returns all weeks and matches for the season, including team schedules.
    """
    try:
        # Get all matches for this season from database
        matches_query = """
            SELECT
                m.match_key,
                m.season,
                m.week,
                m.date,
                m.state,
                m.venue_key,
                v.venue_name,
                m.home_team_key,
                ht.team_name as home_name,
                m.away_team_key,
                at.team_name as away_name
            FROM matches m
            LEFT JOIN venues v ON m.venue_key = v.venue_key
            LEFT JOIN teams ht ON m.home_team_key = ht.team_key AND ht.season = m.season
            LEFT JOIN teams at ON m.away_team_key = at.team_key AND at.season = m.season
            WHERE m.season = :season
            ORDER BY m.week, m.match_key
        """
        matches_result = execute_query(matches_query, {"season": season})

        if not matches_result:
            raise HTTPException(
                status_code=404,
                detail=f"Season {season} schedule not found"
            )

        # Get teams for this season
        teams_query = """
            SELECT
                t.team_key,
                t.team_name,
                t.home_venue_key,
                v.venue_name as home_venue_name
            FROM teams t
            LEFT JOIN venues v ON t.home_venue_key = v.venue_key
            WHERE t.season = :season
            ORDER BY t.team_key
        """
        teams_result = execute_query(teams_query, {"season": season})

        # Build teams dict
        teams = {}
        for row in teams_result:
            teams[row['team_key']] = {
                "name": row['team_name'],
                "venue": row['home_venue_key']
            }

        # Group matches by week
        weeks_dict = {}
        for row in matches_result:
            week_num = row['week']
            if week_num not in weeks_dict:
                weeks_dict[week_num] = {
                    "week": week_num,
                    "date": row['date'].strftime("%m/%d/%Y") if row['date'] else None,
                    "matches": []
                }

            match_info = {
                "match_key": row['match_key'],
                "home": row['home_team_key'],
                "away": row['away_team_key'],
                "venue": row['venue_key']
            }
            weeks_dict[week_num]["matches"].append(match_info)

        weeks = [weeks_dict[k] for k in sorted(weeks_dict.keys())]

        return {
            "season": season,
            "weeks": weeks,
            "teams": teams
        }

    except HTTPException:
        raise
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
    Queries from database (works in production without filesystem access).
    """
    try:
        # Build query to get matches from database
        query = """
            SELECT
                m.match_key,
                m.season,
                m.week,
                m.date,
                m.state,
                m.venue_key,
                v.venue_name,
                m.home_team_key as home_key,
                ht.team_name as home_name,
                m.away_team_key as away_key,
                at.team_name as away_name
            FROM matches m
            LEFT JOIN venues v ON m.venue_key = v.venue_key
            LEFT JOIN teams ht ON m.home_team_key = ht.team_key AND ht.season = m.season
            LEFT JOIN teams at ON m.away_team_key = at.team_key AND at.season = m.season
            WHERE m.season = :season
        """
        params = {"season": season}

        if week is not None:
            query += " AND m.week = :week"
            params["week"] = week

        query += " ORDER BY m.week, m.match_key"

        results = execute_query(query, params)

        if not results:
            # Check if season exists at all
            season_check = execute_query(
                "SELECT COUNT(*) as cnt FROM matches WHERE season = :season",
                {"season": season}
            )
            if not season_check or season_check[0]['cnt'] == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Season {season} not found"
                )

        # Format matches for frontend compatibility
        all_matches = []
        for row in results:
            match_info = {
                "match_key": row['match_key'],
                "week": row['week'],
                "week_label": f"WEEK {row['week']}",
                "date": row['date'].strftime("%m/%d/%Y") if row['date'] else None,
                "home_key": row['home_key'],
                "home_name": row['home_name'] or row['home_key'],
                "home_linked": True,
                "away_key": row['away_key'],
                "away_name": row['away_name'] or row['away_key'],
                "away_linked": True,
                "venue": {
                    "key": row['venue_key'],
                    "name": row['venue_name'] or row['venue_key']
                },
                "is_playoffs": row['week'] > 10,  # Weeks 11+ are typically playoffs
                "state": row['state']
            }
            all_matches.append(match_info)

        return {
            "season": season,
            "week": week,
            "matches": all_matches,
            "count": len(all_matches)
        }

    except HTTPException:
        raise
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
    Queries from database (works in production without filesystem access).
    """
    try:
        team_key_upper = team_key.upper()

        # Get team info
        team_query = """
            SELECT t.team_key, t.team_name, t.home_venue_key
            FROM teams t
            WHERE t.team_key = :team_key AND t.season = :season
        """
        team_result = execute_query(team_query, {"team_key": team_key_upper, "season": season})

        if not team_result:
            raise HTTPException(
                status_code=404,
                detail=f"Team {team_key} not found in season {season}"
            )

        team_info = team_result[0]

        # Get team's matches
        matches_query = """
            SELECT
                m.match_key,
                m.week,
                m.date,
                m.venue_key,
                m.home_team_key,
                m.away_team_key,
                m.state,
                ht.team_name as home_name,
                at.team_name as away_name
            FROM matches m
            LEFT JOIN teams ht ON m.home_team_key = ht.team_key AND ht.season = m.season
            LEFT JOIN teams at ON m.away_team_key = at.team_key AND at.season = m.season
            WHERE m.season = :season
            AND (m.home_team_key = :team_key OR m.away_team_key = :team_key)
            ORDER BY m.week
        """
        matches_result = execute_query(matches_query, {"team_key": team_key_upper, "season": season})

        # Build schedule list
        schedule = []
        for row in matches_result:
            is_home = row['home_team_key'] == team_key_upper
            opponent_key = row['away_team_key'] if is_home else row['home_team_key']
            opponent_name = row['away_name'] if is_home else row['home_name']

            schedule.append({
                "week": row['week'],
                "date": row['date'].strftime("%m/%d/%Y") if row['date'] else None,
                "opponent": opponent_key,
                "opponent_name": opponent_name,
                "venue": row['venue_key'],
                "is_home": is_home,
                "state": row['state']
            })

        # Get roster (players who have played for this team in this season)
        roster_query = """
            SELECT DISTINCT s.player_key, p.name as player_name
            FROM scores s
            INNER JOIN players p ON s.player_key = p.player_key
            WHERE s.team_key = :team_key AND s.season = :season
            ORDER BY p.name
        """
        roster_result = execute_query(roster_query, {"team_key": team_key_upper, "season": season})
        roster = [row['player_key'] for row in roster_result]

        return {
            "season": season,
            "team_key": team_key_upper,
            "team_name": team_info['team_name'],
            "home_venue": team_info['home_venue_key'],
            "schedule": schedule,
            "roster": roster
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team {team_key} schedule for season {season}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch team schedule"
        )


@router.get("/matchups-init")
def get_matchups_init():
    """
    Combined endpoint for matchups page initialization.
    Returns seasons, current season status, and matches in a single request.
    This eliminates 3 sequential API calls on page load.
    """
    try:
        # Get available seasons from database
        seasons_query = "SELECT DISTINCT season FROM matches ORDER BY season"
        seasons_result = execute_query(seasons_query, {})
        all_seasons = [row['season'] for row in seasons_result] if seasons_result else []

        # Find the latest season
        latest_season = max(all_seasons) if all_seasons else 23

        # Get season status (inline logic from get_season_status)
        status_query = """
            SELECT
                MIN(date) as first_date,
                MAX(date) as last_date,
                COUNT(*) as total_matches,
                SUM(CASE WHEN state = 'scheduled' THEN 1 ELSE 0 END) as scheduled_matches,
                SUM(CASE WHEN state = 'complete' THEN 1 ELSE 0 END) as completed_matches,
                SUM(CASE WHEN date >= CURRENT_DATE THEN 1 ELSE 0 END) as upcoming_matches
            FROM matches
            WHERE season = :season
        """
        status_result = execute_query(status_query, {"season": latest_season})

        season_status = None
        if status_result and status_result[0]['total_matches'] > 0:
            row = status_result[0]
            first_week_date = row['first_date']
            last_week_date = row['last_date']
            total_matches = row['total_matches']
            upcoming_matches = row['upcoming_matches'] or 0
            completed_matches = row['completed_matches'] or 0

            now = datetime.now()

            if first_week_date is None:
                status = "unknown"
                message = "Unable to determine season dates"
            elif now.date() < first_week_date:
                status = "upcoming"
                message = f"Season {latest_season} starts on {first_week_date.strftime('%B %d, %Y')}"
            elif completed_matches == total_matches:
                status = "completed"
                message = f"Season {latest_season} has completed. Check back for Season {latest_season + 1}!"
            elif now.date() <= last_week_date + timedelta(days=1):
                status = "in_progress"
                message = f"Season {latest_season} is currently in progress with {upcoming_matches} upcoming matches"
            else:
                status = "completed"
                message = f"Season {latest_season} has completed. Check back for Season {latest_season + 1}!"

            season_status = {
                "season": latest_season,
                "status": status,
                "message": message,
                "first_week_date": first_week_date.strftime("%Y-%m-%d") if first_week_date else None,
                "last_week_date": last_week_date.strftime("%Y-%m-%d") if last_week_date else None,
                "total_matches": total_matches,
                "upcoming_matches": upcoming_matches
            }

        # Get matches for the latest season (inline logic from get_season_matches)
        matches_query = """
            SELECT
                m.match_key,
                m.season,
                m.week,
                m.date,
                m.state,
                m.venue_key,
                v.venue_name,
                m.home_team_key as home_key,
                ht.team_name as home_name,
                m.away_team_key as away_key,
                at.team_name as away_name
            FROM matches m
            LEFT JOIN venues v ON m.venue_key = v.venue_key
            LEFT JOIN teams ht ON m.home_team_key = ht.team_key AND ht.season = m.season
            LEFT JOIN teams at ON m.away_team_key = at.team_key AND at.season = m.season
            WHERE m.season = :season
            ORDER BY m.week, m.match_key
        """
        matches_result = execute_query(matches_query, {"season": latest_season})

        all_matches = []
        for row in matches_result or []:
            match_info = {
                "match_key": row['match_key'],
                "week": row['week'],
                "week_label": f"WEEK {row['week']}",
                "date": row['date'].strftime("%m/%d/%Y") if row['date'] else None,
                "home_key": row['home_key'],
                "home_name": row['home_name'] or row['home_key'],
                "home_linked": True,
                "away_key": row['away_key'],
                "away_name": row['away_name'] or row['away_key'],
                "away_linked": True,
                "venue": {
                    "key": row['venue_key'],
                    "name": row['venue_name'] or row['venue_key']
                },
                "is_playoffs": row['week'] > 10,
                "state": row['state']
            }
            all_matches.append(match_info)

        return {
            "seasons": all_seasons,
            "current_season": latest_season,
            "season_status": season_status,
            "matches": all_matches
        }

    except Exception as e:
        logger.error(f"Error in matchups-init: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize matchups page"
        )
