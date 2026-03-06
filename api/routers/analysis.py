"""
Weekly Analysis API endpoints

Provides weekly recap data:
- Match summary (home/away win %)
- Upsets (lower avg-IPR team wins)
- Away team wins
- Round 4 comebacks
- Machine score outliers (95th+ percentile)
- Most played machines
- Group standings with POPS
"""

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import execute_query
from api.models.schemas import WeeklyRecap

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

# Max points possible for one team per match:
#   Doubles R1: 4 games × 5 pts = 20
#   Singles R2: 7 games × 3 pts = 21
#   Singles R3: 7 games × 3 pts = 21
#   Doubles R4: 4 games × 5 pts = 20
#   Total = 82

# Threshold for "significant" upset: ≥1.0 average IPR gap (scale is 1–6)
UPSET_IPR_THRESHOLD = 1.0


def _get_archive_path(season: int) -> Path:
    """Return the path to the season matches directory in the data archive."""
    from etl.config import config

    return config.get_matches_path(season)


def _tally_round_points(rounds: list[dict]) -> tuple[list[float], list[float]]:
    """Compute cumulative home/away points after each of the 4 rounds."""
    home_after = [0.0, 0.0, 0.0, 0.0]
    away_after = [0.0, 0.0, 0.0, 0.0]

    for round_data in rounds:
        rn = round_data.get("n", 0)
        if rn < 1 or rn > 4:
            continue
        idx = rn - 1
        for game in round_data.get("games", []):
            home_after[idx] += float(game.get("home_points", 0) or 0)
            away_after[idx] += float(game.get("away_points", 0) or 0)

    for i in range(1, 4):
        home_after[i] += home_after[i - 1]
        away_after[i] += away_after[i - 1]

    return home_after, away_after


def _detect_comeback(match: dict, home_after: list[float], away_after: list[float]) -> dict | None:
    """If the match had a R4 comeback, return the comeback dict; otherwise None."""
    home_after_r3 = home_after[2]
    away_after_r3 = away_after[2]
    home_final = home_after[3]
    away_final = away_after[3]

    if home_final == away_final:
        return None

    home_key = match.get("home", {}).get("key", "")
    away_key = match.get("away", {}).get("key", "")
    home_name = match.get("home", {}).get("name", home_key)
    away_name = match.get("away", {}).get("name", away_key)

    if home_final > away_final and home_after_r3 < away_after_r3:
        deficit = away_after_r3 - home_after_r3
        cb_key, cb_name, ot_key, ot_name = home_key, home_name, away_key, away_name
    elif away_final > home_final and away_after_r3 < home_after_r3:
        deficit = home_after_r3 - away_after_r3
        cb_key, cb_name, ot_key, ot_name = away_key, away_name, home_key, home_name
    else:
        return None

    home_r4 = home_final - home_after_r3
    away_r4 = away_final - away_after_r3
    cb_r4 = home_r4 if cb_key == home_key else away_r4
    ot_r4 = away_r4 if cb_key == home_key else home_r4

    return {
        "match_key": match.get("key", ""),
        "home_team_key": home_key,
        "away_team_key": away_key,
        "comeback_team_key": cb_key,
        "comeback_team_name": cb_name,
        "other_team_key": ot_key,
        "other_team_name": ot_name,
        "deficit_after_r3": round(deficit, 1),
        "comeback_r4_points": round(cb_r4, 1),
        "other_r4_points": round(ot_r4, 1),
        "final_score_comeback": round(home_final if cb_key == home_key else away_final, 1),
        "final_score_other": round(away_final if cb_key == home_key else home_final, 1),
        "venue_key": match.get("venue", {}).get("key", ""),
    }


def _parse_comebacks(season: int, week: int) -> list[dict]:
    """
    Parse match JSON files for the week and identify Round 4 comebacks.

    A comeback is when a team was trailing after Round 3 (rounds 1+2+3 complete)
    but won the match overall. Returns empty list if files are not accessible.
    """
    try:
        matches_path = _get_archive_path(season)
        if not matches_path.exists():
            logger.warning(f"Archive path not accessible: {matches_path}")
            return []

        comebacks = []

        for match_file in matches_path.glob("*.json"):
            try:
                with open(match_file) as f:
                    match = json.load(f)
            except Exception:
                continue

            if int(match.get("week", 0)) != week:
                continue
            if match.get("state") != "complete":
                continue
            if len(match.get("rounds", [])) < 4:
                continue

            home_after, away_after = _tally_round_points(match["rounds"])
            comeback = _detect_comeback(match, home_after, away_after)
            if comeback:
                comebacks.append(comeback)

        comebacks.sort(key=lambda x: x["deficit_after_r3"], reverse=True)
        return comebacks

    except Exception as e:
        logger.warning(f"Could not parse comebacks from JSON files: {e}")
        return []


@router.get(
    "/weekly-recap/weeks",
    summary="Available weeks for weekly recap",
    description="Returns list of weeks that have completed matches for the given season.",
)
def get_available_weeks(
    season: int = Query(..., description="Season number (e.g., 23)"),
):
    rows = execute_query(
        "SELECT DISTINCT week FROM matches WHERE season = :season AND state = 'complete' ORDER BY week",
        {"season": season},
    )
    return [r["week"] for r in rows] if rows else []


@router.get(
    "/weekly-recap",
    response_model=WeeklyRecap,
    summary="Weekly analysis recap",
    description=(
        "Comprehensive weekly recap including upsets, away wins, comebacks, "
        "score outliers, machine popularity, and group standings."
    ),
)
def get_weekly_recap(
    season: int = Query(..., description="Season number (e.g., 23)"),
    week: int | None = Query(
        None, description="Week number — defaults to most recent completed week"
    ),
):
    # Resolve default week
    if week is None:
        rows = execute_query(
            "SELECT MAX(week) as w FROM matches WHERE season = :season AND state = 'complete'",
            {"season": season},
        )
        if not rows or rows[0]["w"] is None:
            raise HTTPException(
                status_code=404, detail=f"No completed matches found for season {season}"
            )
        week = rows[0]["w"]

    # Verify the week has data
    week_check = execute_query(
        "SELECT COUNT(*) as cnt FROM matches WHERE season = :season AND week = :week AND state = 'complete'",
        {"season": season, "week": week},
    )
    if not week_check or week_check[0]["cnt"] == 0:
        raise HTTPException(
            status_code=404, detail=f"No completed matches found for season {season} week {week}"
        )

    # -------------------------------------------------------------------------
    # 1. Match summary (with shared-venue adjustment)
    # -------------------------------------------------------------------------
    summary_rows = execute_query(
        """
        SELECT
            COUNT(*) as total_matches,
            COUNT(*) FILTER (WHERE m.home_team_points > m.away_team_points) as home_wins,
            COUNT(*) FILTER (WHERE m.away_team_points > m.home_team_points) as away_wins,
            COUNT(*) FILTER (WHERE m.home_team_points = m.away_team_points) as ties,
            COUNT(*) FILTER (WHERE at.home_venue_key = m.venue_key) as shared_venue_matches,
            COUNT(*) FILTER (
                WHERE m.home_team_points > m.away_team_points
                AND at.home_venue_key != m.venue_key
            ) as true_home_wins,
            COUNT(*) FILTER (
                WHERE m.away_team_points > m.home_team_points
                AND at.home_venue_key != m.venue_key
            ) as true_away_wins
        FROM matches m
        JOIN teams at ON m.away_team_key = at.team_key AND m.season = at.season
        WHERE m.season = :season AND m.week = :week AND m.state = 'complete'
        """,
        {"season": season, "week": week},
    )
    sr = summary_rows[0]
    total = sr["total_matches"] or 0
    shared = sr["shared_venue_matches"] or 0
    non_shared = total - shared
    match_summary = {
        "total_matches": total,
        "home_wins": sr["home_wins"] or 0,
        "away_wins": sr["away_wins"] or 0,
        "ties": sr["ties"] or 0,
        "home_win_pct": round((sr["home_wins"] or 0) / total * 100, 1) if total > 0 else 0.0,
        "away_win_pct": round((sr["away_wins"] or 0) / total * 100, 1) if total > 0 else 0.0,
        "shared_venue_matches": shared,
    }
    if shared > 0:
        match_summary["true_home_wins"] = sr["true_home_wins"] or 0
        match_summary["true_away_wins"] = sr["true_away_wins"] or 0
        match_summary["true_home_win_pct"] = (
            round((sr["true_home_wins"] or 0) / non_shared * 100, 1) if non_shared > 0 else 0.0
        )
        match_summary["true_away_win_pct"] = (
            round((sr["true_away_wins"] or 0) / non_shared * 100, 1) if non_shared > 0 else 0.0
        )

    # -------------------------------------------------------------------------
    # 2. Upsets + 3. Away wins — computed together from per-match IPR data
    # -------------------------------------------------------------------------
    match_detail_rows = execute_query(
        """
        WITH team_avg_ipr AS (
            SELECT
                match_key,
                team_key,
                AVG(player_ipr) AS avg_ipr
            FROM scores
            WHERE season = :season
              AND week = :week
              AND player_ipr IS NOT NULL
              AND (is_substitute IS NULL OR is_substitute = false)
            GROUP BY match_key, team_key
        )
        SELECT
            m.match_key,
            m.home_team_key,
            ht.team_name AS home_team_name,
            m.away_team_key,
            at2.team_name AS away_team_name,
            m.home_team_points,
            m.away_team_points,
            m.venue_key,
            hi.avg_ipr AS home_avg_ipr,
            ai.avg_ipr AS away_avg_ipr,
            CASE
                WHEN m.home_team_points > m.away_team_points THEN 'home'
                WHEN m.away_team_points > m.home_team_points THEN 'away'
                ELSE 'tie'
            END AS winner,
            CASE WHEN at2.home_venue_key = m.venue_key THEN true ELSE false END AS is_shared_venue
        FROM matches m
        JOIN teams ht ON m.home_team_key = ht.team_key AND m.season = ht.season
        JOIN teams at2 ON m.away_team_key = at2.team_key AND m.season = at2.season
        LEFT JOIN team_avg_ipr hi
            ON m.match_key = hi.match_key AND hi.team_key = m.home_team_key
        LEFT JOIN team_avg_ipr ai
            ON m.match_key = ai.match_key AND ai.team_key = m.away_team_key
        WHERE m.season = :season AND m.week = :week AND m.state = 'complete'
        ORDER BY m.match_key
        """,
        {"season": season, "week": week},
    )

    upsets = []
    away_wins = []

    for row in match_detail_rows:
        home_ipr = row["home_avg_ipr"]
        away_ipr = row["away_avg_ipr"]
        winner = row["winner"]
        ipr_gap = abs((home_ipr or 0) - (away_ipr or 0)) if (home_ipr and away_ipr) else None

        is_shared_venue = row["is_shared_venue"]
        base = {
            "match_key": row["match_key"],
            "home_team_key": row["home_team_key"],
            "home_team_name": row["home_team_name"],
            "away_team_key": row["away_team_key"],
            "away_team_name": row["away_team_name"],
            "home_team_points": float(row["home_team_points"] or 0),
            "away_team_points": float(row["away_team_points"] or 0),
            "home_avg_ipr": round(home_ipr, 2) if home_ipr else None,
            "away_avg_ipr": round(away_ipr, 2) if away_ipr else None,
            "ipr_gap": round(ipr_gap, 2) if ipr_gap is not None else None,
            "winner": winner,
            "venue_key": row["venue_key"],
            "is_shared_venue": is_shared_venue,
        }

        # Away win tracking
        if winner == "away":
            away_wins.append(
                {**base, "is_underdog": bool(away_ipr and home_ipr and away_ipr < home_ipr)}
            )

        # Upset: lower-rated team wins with significant IPR gap
        if ipr_gap is not None and ipr_gap >= UPSET_IPR_THRESHOLD:
            if winner == "home" and home_ipr < away_ipr:
                upsets.append(
                    {
                        **base,
                        "upset_team_key": row["home_team_key"],
                        "upset_team_name": row["home_team_name"],
                    }
                )
            elif winner == "away" and away_ipr < home_ipr:
                upsets.append(
                    {
                        **base,
                        "upset_team_key": row["away_team_key"],
                        "upset_team_name": row["away_team_name"],
                    }
                )

    upsets.sort(key=lambda x: x["ipr_gap"] or 0, reverse=True)
    away_wins.sort(key=lambda x: (x["is_underdog"], x["ipr_gap"] or 0), reverse=True)

    # -------------------------------------------------------------------------
    # 4. Round 4 comebacks — parse from match JSON archive
    # -------------------------------------------------------------------------
    comebacks = _parse_comebacks(season, week)

    # -------------------------------------------------------------------------
    # 5. Score outliers (95th+ percentile)
    # -------------------------------------------------------------------------
    outlier_rows = execute_query(
        """
        WITH thresholds AS (
            SELECT
                machine_key,
                MAX(score_threshold) FILTER (WHERE percentile = 95) AS p95,
                MAX(score_threshold) FILTER (WHERE percentile = 99) AS p99
            FROM score_percentiles
            WHERE venue_key = '_ALL_' AND season = :season
            GROUP BY machine_key
        )
        SELECT
            s.match_key,
            s.player_key,
            p.name AS player_name,
            s.team_key,
            t.team_name,
            s.machine_key,
            m.machine_name,
            s.score,
            s.round_number,
            s.player_position,
            th.p95,
            th.p99,
            CASE WHEN s.score >= th.p99 THEN 99 ELSE 95 END AS pctile_floor
        FROM scores s
        JOIN players p ON s.player_key = p.player_key
        JOIN teams t ON s.team_key = t.team_key AND s.season = t.season
        JOIN machines m ON s.machine_key = m.machine_key
        JOIN thresholds th ON s.machine_key = th.machine_key
        WHERE s.season = :season
          AND s.week = :week
          AND th.p95 IS NOT NULL
          AND s.score >= th.p95
          AND NOT (s.round_number IN (1, 4) AND s.player_position = 4)
        ORDER BY pctile_floor DESC, s.score DESC
        """,
        {"season": season, "week": week},
    )

    score_outliers = [
        {
            "match_key": r["match_key"],
            "player_key": r["player_key"],
            "player_name": r["player_name"],
            "team_key": r["team_key"],
            "team_name": r["team_name"],
            "machine_key": r["machine_key"],
            "machine_name": r["machine_name"],
            "score": r["score"],
            "round_number": r["round_number"],
            "player_position": r["player_position"],
            "p95_threshold": r["p95"],
            "p99_threshold": r["p99"],
            "pctile_floor": r["pctile_floor"],
        }
        for r in outlier_rows
    ]

    # -------------------------------------------------------------------------
    # 6. Most played machines
    # -------------------------------------------------------------------------
    machine_rows = execute_query(
        """
        SELECT
            s.machine_key,
            m.machine_name,
            COUNT(*) AS games_played,
            COUNT(DISTINCT s.match_key) AS matches_played
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE s.season = :season AND s.week = :week
        GROUP BY s.machine_key, m.machine_name
        ORDER BY games_played DESC
        LIMIT 15
        """,
        {"season": season, "week": week},
    )
    top_machines = [dict(r) for r in machine_rows]

    # -------------------------------------------------------------------------
    # 7. Group standings with POPS
    # POPS = avg of (team_pts / match_total) per match
    # -------------------------------------------------------------------------
    standings_rows = execute_query(
        """
        SELECT
            t.division,
            t.team_key,
            t.team_name,
            COUNT(m.match_key) AS matches_played,
            COUNT(*) FILTER (
                WHERE (m.home_team_key = t.team_key AND m.home_team_points > m.away_team_points)
                   OR (m.away_team_key = t.team_key AND m.away_team_points > m.home_team_points)
            ) AS wins,
            COUNT(*) FILTER (
                WHERE (m.home_team_key = t.team_key AND m.home_team_points < m.away_team_points)
                   OR (m.away_team_key = t.team_key AND m.away_team_points < m.home_team_points)
            ) AS losses,
            COUNT(*) FILTER (
                WHERE m.home_team_points = m.away_team_points
            ) AS ties,
            SUM(
                CASE
                    WHEN m.home_team_key = t.team_key THEN COALESCE(m.home_team_points, 0)
                    ELSE COALESCE(m.away_team_points, 0)
                END
            ) AS total_points_earned,
            SUM(
                CASE
                    WHEN (m.home_team_points + m.away_team_points) > 0 THEN
                        CASE
                            WHEN m.home_team_key = t.team_key
                                THEN m.home_team_points::float / (m.home_team_points + m.away_team_points)
                            ELSE m.away_team_points::float / (m.home_team_points + m.away_team_points)
                        END
                    ELSE 0
                END
            ) AS pct_total
        FROM teams t
        JOIN matches m
            ON (m.home_team_key = t.team_key OR m.away_team_key = t.team_key)
            AND m.season = t.season
        WHERE t.season = :season
          AND m.state = 'complete'
          AND t.division IS NOT NULL
        GROUP BY t.division, t.team_key, t.team_name
        ORDER BY t.division, wins DESC, total_points_earned DESC
        """,
        {"season": season},
    )

    group_standings = []
    for r in standings_rows:
        mp = r["matches_played"] or 0
        earned = float(r["total_points_earned"] or 0)
        pct_total = float(r["pct_total"] or 0)
        pops = round(pct_total / mp, 3) if mp > 0 else 0.0
        group_standings.append(
            {
                "division": r["division"],
                "team_key": r["team_key"],
                "team_name": r["team_name"],
                "matches_played": mp,
                "wins": r["wins"] or 0,
                "losses": r["losses"] or 0,
                "ties": r["ties"] or 0,
                "total_points_earned": earned,
                "pops": pops,
            }
        )

    return WeeklyRecap(
        season=season,
        week=week,
        match_summary=match_summary,
        upsets=upsets,
        away_wins=away_wins,
        comebacks=comebacks,
        score_outliers=score_outliers,
        top_machines=top_machines,
        group_standings=group_standings,
    )
