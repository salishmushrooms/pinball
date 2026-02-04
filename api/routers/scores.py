"""
Scores API endpoints - Browse and filter score data
"""
from typing import Optional, List
import logging
from fastapi import APIRouter, Query, HTTPException

from api.models.schemas import (
    ScoreItem,
    MachineScoreStats,
    MachineScoreGroup,
    ScoreBrowseResponse,
    MachineScoresResponse,
    ErrorResponse,
)
from api.dependencies import execute_query

router = APIRouter(prefix="/scores", tags=["scores"])
logger = logging.getLogger(__name__)


@router.get(
    "/browse",
    response_model=ScoreBrowseResponse,
    summary="Browse scores with filtering",
    description="Get scores grouped by machine with aggregate stats. Always groups by machine since scores cannot be compared across machines."
)
def browse_scores(
    seasons: List[int] = Query(..., description="Season(s) to include (required)"),
    teams: Optional[List[str]] = Query(None, description="Filter by team key(s)"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    machine_keys: Optional[List[str]] = Query(None, description="Filter by machine key(s)"),
    include_all_venues: bool = Query(False, description="When venue_key is set, include scores from all venues for those machines"),
    scores_per_machine: int = Query(20, ge=1, le=100, description="Number of scores to return per machine group"),
):
    """
    Browse scores with filtering, grouped by machine.

    Key features:
    - Always groups by machine (scores can't be compared across machines)
    - Returns aggregate stats (count, median, min, max) per machine
    - Supports filtering by season, team, venue, and machine
    - Special mode: set venue_key + include_all_venues=true to see all scores
      for machines at that venue, regardless of where the scores were recorded

    Example queries:
    - `/scores/browse?seasons=23&seasons=22` - All scores from seasons 22-23
    - `/scores/browse?seasons=23&teams=SKP&teams=TRL&venue_key=T4B` - Compare two teams at a venue
    - `/scores/browse?seasons=23&venue_key=T4B&include_all_venues=true` - All scores on T4B machines, any venue
    """
    # Build the base query parameters
    params = {"seasons": seasons}
    where_clauses = ["s.season = ANY(:seasons)"]

    # Team filter
    if teams:
        where_clauses.append("s.team_key = ANY(:teams)")
        params["teams"] = teams

    # Machine filter (either explicit or derived from venue)
    machine_filter_keys = None
    if machine_keys:
        machine_filter_keys = machine_keys
    elif venue_key and include_all_venues:
        # Get machines at the venue, but don't filter scores by venue
        machine_query = """
            SELECT machine_key FROM venue_machines
            WHERE venue_key = :venue_key
            AND season = (SELECT MAX(season) FROM venue_machines WHERE venue_key = :venue_key)
            AND active = true
        """
        machine_result = execute_query(machine_query, {"venue_key": venue_key})
        if machine_result:
            machine_filter_keys = [row["machine_key"] for row in machine_result]

    if machine_filter_keys:
        where_clauses.append("s.machine_key = ANY(:machine_keys)")
        params["machine_keys"] = machine_filter_keys

    # Venue filter (only if not using include_all_venues mode)
    if venue_key and not include_all_venues:
        where_clauses.append("s.venue_key = :venue_key")
        params["venue_key"] = venue_key

    where_clause = " AND ".join(where_clauses)

    # First, get aggregate stats per machine
    stats_query = f"""
        SELECT
            s.machine_key,
            m.machine_name,
            COUNT(*) as count,
            CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.score) AS BIGINT) as median,
            MIN(s.score) as min,
            MAX(s.score) as max
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE {where_clause}
        GROUP BY s.machine_key, m.machine_name
        ORDER BY m.machine_name
    """
    stats_result = execute_query(stats_query, params)

    if not stats_result:
        return ScoreBrowseResponse(
            total_score_count=0,
            filters_applied={
                "seasons": seasons,
                "teams": teams,
                "venue_key": venue_key,
                "machine_keys": machine_keys,
                "include_all_venues": include_all_venues,
            },
            machine_groups=[],
        )

    # Calculate total score count
    total_score_count = sum(row["count"] for row in stats_result)

    # Now get the first N scores per machine
    # Using a window function to rank scores within each machine
    scores_query = f"""
        WITH ranked_scores AS (
            SELECT
                s.score,
                s.player_key,
                p.name as player_name,
                s.team_key,
                t.team_name,
                s.venue_key,
                v.venue_name,
                s.season,
                s.round_number as round,
                s.machine_key,
                s.date,
                ROW_NUMBER() OVER (PARTITION BY s.machine_key ORDER BY s.score DESC) as rn
            FROM scores s
            JOIN players p ON s.player_key = p.player_key
            JOIN teams t ON s.team_key = t.team_key AND t.season = s.season
            JOIN venues v ON s.venue_key = v.venue_key
            WHERE {where_clause}
        )
        SELECT * FROM ranked_scores
        WHERE rn <= :scores_limit
        ORDER BY machine_key, score DESC
    """
    params["scores_limit"] = scores_per_machine
    scores_result = execute_query(scores_query, params)

    # Group scores by machine
    scores_by_machine = {}
    for row in scores_result or []:
        machine_key = row["machine_key"]
        if machine_key not in scores_by_machine:
            scores_by_machine[machine_key] = []
        scores_by_machine[machine_key].append(
            ScoreItem(
                score=row["score"],
                player_key=row["player_key"],
                player_name=row["player_name"],
                team_key=row["team_key"],
                team_name=row["team_name"],
                venue_key=row["venue_key"],
                venue_name=row["venue_name"],
                date=row["date"].strftime("%Y-%m-%d") if row["date"] else None,
                season=row["season"],
                round=row["round"],
            )
        )

    # Build machine groups
    machine_groups = []
    for stat_row in stats_result:
        machine_key = stat_row["machine_key"]
        count = stat_row["count"]
        scores = scores_by_machine.get(machine_key, [])

        machine_groups.append(
            MachineScoreGroup(
                machine_key=machine_key,
                machine_name=stat_row["machine_name"],
                stats=MachineScoreStats(
                    count=count,
                    median=stat_row["median"] or 0,
                    min=stat_row["min"] or 0,
                    max=stat_row["max"] or 0,
                ),
                scores=scores,
                has_more=count > scores_per_machine,
            )
        )

    return ScoreBrowseResponse(
        total_score_count=total_score_count,
        filters_applied={
            "seasons": seasons,
            "teams": teams,
            "venue_key": venue_key,
            "machine_keys": machine_filter_keys or machine_keys,
            "include_all_venues": include_all_venues,
        },
        machine_groups=machine_groups,
    )


@router.get(
    "/browse/{machine_key}",
    response_model=MachineScoresResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Load more scores for a specific machine",
    description="Paginate through scores for a specific machine with the same filters applied"
)
def browse_machine_scores(
    machine_key: str,
    seasons: List[int] = Query(..., description="Season(s) to include (required)"),
    teams: Optional[List[str]] = Query(None, description="Filter by team key(s)"),
    venue_key: Optional[str] = Query(None, description="Filter by venue"),
    include_all_venues: bool = Query(False, description="When venue_key is set, include scores from all venues"),
    limit: int = Query(50, ge=1, le=100, description="Number of scores to return"),
    offset: int = Query(0, ge=0, description="Number of scores to skip"),
):
    """
    Load more scores for a specific machine with pagination.

    Uses the same filters as /scores/browse but returns scores for a single machine
    with offset-based pagination.

    Example: `/scores/browse/AFM?seasons=23&teams=SKP&limit=50&offset=20`
    """
    # Verify machine exists
    machine_query = "SELECT machine_name FROM machines WHERE machine_key = :machine_key"
    machine_result = execute_query(machine_query, {"machine_key": machine_key})
    if not machine_result:
        raise HTTPException(status_code=404, detail=f"Machine '{machine_key}' not found")

    machine_name = machine_result[0]["machine_name"]

    # Build query parameters
    params = {
        "seasons": seasons,
        "machine_key": machine_key,
    }
    where_clauses = [
        "s.season = ANY(:seasons)",
        "s.machine_key = :machine_key",
    ]

    if teams:
        where_clauses.append("s.team_key = ANY(:teams)")
        params["teams"] = teams

    if venue_key and not include_all_venues:
        where_clauses.append("s.venue_key = :venue_key")
        params["venue_key"] = venue_key

    where_clause = " AND ".join(where_clauses)

    # Get total count
    count_query = f"""
        SELECT COUNT(*) as total FROM scores s WHERE {where_clause}
    """
    count_result = execute_query(count_query, params)
    total_count = count_result[0]["total"] if count_result else 0

    # Get paginated scores
    scores_query = f"""
        SELECT
            s.score,
            s.player_key,
            p.name as player_name,
            s.team_key,
            t.team_name,
            s.venue_key,
            v.venue_name,
            s.season,
            s.round_number as round,
            s.date
        FROM scores s
        JOIN players p ON s.player_key = p.player_key
        JOIN teams t ON s.team_key = t.team_key AND t.season = s.season
        JOIN venues v ON s.venue_key = v.venue_key
        WHERE {where_clause}
        ORDER BY s.score DESC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = limit
    params["offset"] = offset
    scores_result = execute_query(scores_query, params)

    scores = [
        ScoreItem(
            score=row["score"],
            player_key=row["player_key"],
            player_name=row["player_name"],
            team_key=row["team_key"],
            team_name=row["team_name"],
            venue_key=row["venue_key"],
            venue_name=row["venue_name"],
            date=row["date"].strftime("%Y-%m-%d") if row["date"] else None,
            season=row["season"],
            round=row["round"],
        )
        for row in scores_result or []
    ]

    return MachineScoresResponse(
        machine_key=machine_key,
        machine_name=machine_name,
        total_count=total_count,
        scores=scores,
    )
