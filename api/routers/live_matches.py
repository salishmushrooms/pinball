"""
Live match data endpoints

Fetches current match scores from mondaynightpinball.com and enriches
them with historical score percentiles from the MNP Analyzer database.
"""

import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Query

from api.config import CURRENT_SEASON
from api.dependencies import execute_query
from api.models.schemas import (
    LiveGame,
    LiveMatchDetail,
    LiveMatchSummary,
    LiveRosterPlayer,
    LiveRound,
    LiveScore,
    LiveWeekResponse,
)

router = APIRouter(prefix="/live", tags=["live"])
logger = logging.getLogger(__name__)

MNP_MAIN_BASE = "https://mondaynightpinball.com"

# In-memory caches with TTL
# Structure: {key: {"data": ..., "expires": datetime}}
_match_cache: dict[str, dict] = {}
_week_cache: dict[str, dict] = {}

ACTIVE_TTL = timedelta(seconds=30)
COMPLETE_TTL = timedelta(minutes=10)
WEEK_TTL = timedelta(seconds=60)


def _get_current_week(season: int) -> int:
    """Get the most recently played week from the DB based on today's date."""
    results = execute_query(
        "SELECT week FROM matches WHERE season = :season AND date <= CURRENT_DATE "
        "ORDER BY date DESC LIMIT 1",
        {"season": season},
    )
    return results[0]["week"] if results else 1


def _get_week_matches_from_db(season: int, week: int) -> list[dict]:
    """Fetch all match rows for a given week, joining team names."""
    return execute_query(
        """
        SELECT
            m.match_key, m.week, m.date,
            m.away_team_key, t1.team_name AS away_team_name,
            m.home_team_key, t2.team_name AS home_team_name,
            m.venue_key
        FROM matches m
        LEFT JOIN teams t1 ON t1.team_key = m.away_team_key AND t1.season = m.season
        LEFT JOIN teams t2 ON t2.team_key = m.home_team_key AND t2.season = m.season
        WHERE m.season = :season AND m.week = :week
        ORDER BY m.match_key
        """,
        {"season": season, "week": week},
    )


def _to_main_site_key(match_key: str) -> str:
    """Convert a DB match key to the main-site format.

    DB may store:   mnp-23-05-adb-ttt  (zero-padded week, lowercase teams)
    Main site uses: mnp-23-5-ADB-TTT   (no padding, uppercase teams)
    """
    parts = match_key.split("-")
    if len(parts) >= 5:
        season = parts[1]
        week = str(int(parts[2]))  # strip zero-padding
        away = parts[3].upper()
        home = parts[4].upper()
        return f"mnp-{season}-{week}-{away}-{home}"
    return match_key


async def _fetch_match_json(match_key: str) -> dict | None:
    """
    Fetch a match's JSON from mondaynightpinball.com.
    Returns None on any error (404, timeout, network failure).
    """
    site_key = _to_main_site_key(match_key)
    url = f"{MNP_MAIN_BASE}/matches/{site_key}.json"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            return data
    except Exception as e:
        logger.warning(f"Failed to fetch match {match_key} from main site: {e}")
        return None


def _parse_state(raw: dict) -> str:
    """Return normalized uppercase state string from raw match JSON."""
    state = raw.get("state", "")
    return state.upper() if isinstance(state, str) else "UNKNOWN"


def _compute_totals(raw: dict) -> tuple[int, int]:
    """Sum away_points and home_points across all games in all rounds."""
    away = home = 0
    for rd in raw.get("rounds", []):
        for game in rd.get("games", []):
            away += game.get("away_points", 0) or 0
            home += game.get("home_points", 0) or 0
    return away, home


def _date_str(db_match: dict) -> str | None:
    val = db_match.get("date")
    if val is None:
        return None
    return val.isoformat() if hasattr(val, "isoformat") else str(val)


# ---------------------------------------------------------------------------
# Handicap / bonus point calculation
# Ported from model/matches.js in mondaynightpinball.com
# ---------------------------------------------------------------------------


def _ipr_for_player(player: dict) -> float:
    """Return a player's effective IPR, minimum 1. Mirrors JS iprForPlayer()."""
    ipr = player.get("IPR")
    if isinstance(ipr, (int, float)) and ipr == ipr:  # finite check (NaN != NaN)
        return max(1.0, float(ipr))
    rating = player.get("rating")
    if isinstance(rating, (int, float)) and rating == rating:
        return max(1.0, float(rating))
    return 1.0


def _get_calculated_team_ipr(lineup: list[dict]) -> float:
    """
    Calculate the composite team IPR used for handicap.
    Mirrors Team.getCalculatedTeamIPR() in model/matches.js.

    For 10-player lineups: returns the plain sum of all player IPRs.
    For smaller lineups (3-9): adds top-3 average and optionally top 4-6 average
    as extra weighting (this path is rarely used in season play).
    """
    sorted_lineup = sorted(lineup, key=_ipr_for_player, reverse=True)
    team_ipr = sum(_ipr_for_player(p) for p in sorted_lineup)

    n = len(sorted_lineup)
    if 2 < n < 10:
        team_ipr += sum(_ipr_for_player(sorted_lineup[i]) for i in range(3)) / 3
    if 5 < n < 9:
        team_ipr += sum(_ipr_for_player(sorted_lineup[i]) for i in range(3, 6)) / 3

    return team_ipr


def _calculate_bonus(lineup: list[dict]) -> dict:
    """
    Calculate participation bonus and handicap points for a team lineup.
    Mirrors Team.getBonus() in model/matches.js.

    Returns {"participation": int, "handicap": int}.
    Both are 0 until the match is complete (30 total player-rounds).

    Handicap formula: trunc((50 - teamIPR) / 2), scaled by playerRounds/30,
    clamped to [0, 15].

    Participation: 9 pts if all 10 players played 3+ rounds; 4 pts if 9 did.
    """
    bonus = {"participation": 0, "handicap": 0}
    player_rounds = 0
    player_rounds_ipr = 0.0
    played0 = played1 = played3 = 0
    team_ipr = _get_calculated_team_ipr(lineup)
    num_players = len(lineup)

    for p in lineup:
        n = int(p.get("num_played") or 0)
        player_rounds += n
        player_rounds_ipr += n * _ipr_for_player(p)
        if n >= 3:
            played3 += 1
        if n == 1:
            played1 += 1
        if n == 0:
            played0 += 1

    # No bonus until the match is complete (30 player-rounds: 8+7+7+8)
    if player_rounds < 30:
        return bonus

    handicap = 0.0
    # These branches mirror the JS exactly (playerRounds < 15 is unreachable
    # after the < 30 guard, but kept for parity)
    if player_rounds < 15:
        handicap = (50 - team_ipr) / 2
    if num_players == 10:  # noqa: SIM102
        if (
            player_rounds < 22
            and played0 == 0
            or player_rounds < 30
            and played0 == 0
            and played1 == 0
            or player_rounds == 30
            and played3 == 10
        ):
            handicap = (50 - team_ipr) / 2
    if handicap == 0:
        team_ipr_partial = (player_rounds_ipr * 10) / player_rounds
        handicap = (50 - team_ipr_partial) / 2

    handicap *= player_rounds / 30
    handicap = int(handicap)  # trunc (matches JS Math.trunc)
    handicap = max(0, min(15, handicap))

    if played3 == 10:
        bonus["participation"] = 9
    elif played3 == 9:
        bonus["participation"] = 4

    bonus["handicap"] = handicap
    return bonus


def _build_summary(db_match: dict, raw: dict | None) -> LiveMatchSummary:
    """Build a LiveMatchSummary from a DB row and optional live JSON."""
    if raw is None:
        state = "UNAVAILABLE"
        away_total = home_total = 0
        current_round = 0
        away_handicap = home_handicap = 0
        away_participation = home_participation = 0
    else:
        state = _parse_state(raw)
        away_total, home_total = _compute_totals(raw)
        current_round = int(raw.get("round", 0) or 0)

        away_bonus = _calculate_bonus(raw.get("away", {}).get("lineup", []))
        home_bonus = _calculate_bonus(raw.get("home", {}).get("lineup", []))
        away_handicap = away_bonus["handicap"]
        away_participation = away_bonus["participation"]
        home_handicap = home_bonus["handicap"]
        home_participation = home_bonus["participation"]

    return LiveMatchSummary(
        match_key=db_match["match_key"],
        week=db_match["week"],
        away_team_key=db_match["away_team_key"],
        away_team_name=db_match.get("away_team_name") or db_match["away_team_key"],
        home_team_key=db_match["home_team_key"],
        home_team_name=db_match.get("home_team_name") or db_match["home_team_key"],
        venue_key=db_match["venue_key"],
        date=_date_str(db_match),
        state=state,
        away_total_points=away_total,
        home_total_points=home_total,
        away_handicap=away_handicap,
        away_participation=away_participation,
        home_handicap=home_handicap,
        home_participation=home_participation,
        away_final_points=away_total + away_handicap + away_participation,
        home_final_points=home_total + home_handicap + home_participation,
        current_round=current_round,
    )


def _get_machine_names(machine_keys: list[str]) -> dict[str, str]:
    """Batch-fetch machine display names from the DB."""
    if not machine_keys:
        return {}
    placeholders = ", ".join(f":k{i}" for i in range(len(machine_keys)))
    params = {f"k{i}": k for i, k in enumerate(machine_keys)}
    results = execute_query(
        f"SELECT machine_key, machine_name FROM machines WHERE machine_key IN ({placeholders})",
        params,
    )
    return {r["machine_key"]: r["machine_name"] for r in results}


def _get_percentile_thresholds(machine_keys: list[str]) -> dict[str, list[tuple]]:
    """
    Batch-fetch pre-calculated percentile thresholds for a set of machines.

    Returns {machine_key: [(score_threshold, percentile), ...]} sorted ascending
    by score_threshold so that _score_percentile() can do a linear scan.
    """
    if not machine_keys:
        return {}
    placeholders = ", ".join(f":k{i}" for i in range(len(machine_keys)))
    params = {f"k{i}": k for i, k in enumerate(machine_keys)}
    results = execute_query(
        f"""
        SELECT machine_key, percentile, score_threshold
        FROM score_percentiles
        WHERE machine_key IN ({placeholders}) AND venue_key = '_ALL_'
        ORDER BY machine_key, score_threshold ASC
        """,
        params,
    )
    data: dict[str, list[tuple]] = {}
    for r in results:
        key = r["machine_key"]
        data.setdefault(key, []).append((r["score_threshold"], r["percentile"]))
    return data


def _score_percentile(score: int, thresholds: list[tuple]) -> int:
    """
    Given a score and a list of (score_threshold, percentile) sorted ascending
    by score_threshold, return the highest percentile the score achieves.
    """
    result = 0
    for threshold, pct in thresholds:
        if score >= threshold:
            result = pct
        else:
            break
    return result


def _build_lineup_lookup(raw: dict) -> dict[str, dict]:
    """Build a mapping of player_key → lineup entry from both teams."""
    lookup: dict[str, dict] = {}
    for side in ("away", "home"):
        for p in raw.get(side, {}).get("lineup", []):
            key = p.get("key")
            if key:
                lookup[key] = p
    return lookup


def _build_roster(
    raw: dict,
    side: str,
    player_points: dict[str, float],
) -> list[LiveRosterPlayer]:
    """Build a LiveRosterPlayer list for one team from raw match JSON."""
    team_data = raw.get(side, {})
    lineup = team_data.get("lineup", [])
    captain_keys = {c.get("key") for c in team_data.get("captains", [])}

    roster = []
    for p in lineup:
        key = p.get("key", "")
        ipr_val = p.get("IPR")
        if not isinstance(ipr_val, (int, float)) or ipr_val != ipr_val:
            ipr_val = p.get("rating")
        if not isinstance(ipr_val, (int, float)) or ipr_val != ipr_val:
            ipr_val = None

        roster.append(
            LiveRosterPlayer(
                key=key,
                name=p.get("name", key),
                ipr=float(ipr_val) if ipr_val is not None else None,
                is_sub=bool(p.get("sub", False)),
                is_captain=key in captain_keys,
                num_played=int(p.get("num_played", 0) or 0),
                total_points=player_points.get(key, 0.0),
            )
        )
    return roster


def _build_detail(
    db_match: dict,
    raw: dict,
    machine_names: dict[str, str],
    percentile_data: dict[str, list[tuple]],
) -> LiveMatchDetail:
    """Build a LiveMatchDetail with enriched per-score percentiles."""
    lineup_lookup = _build_lineup_lookup(raw)

    # Track per-player point totals across all games
    player_points: dict[str, float] = {}

    rounds = []
    for rd in raw.get("rounds", []):
        n = rd.get("n", 0)
        # Rounds 1 & 4 are doubles (4 players); 2 & 3 are singles (2 players)
        num_players = 4 if n in (1, 4) else 2
        games = []
        for game in rd.get("games", []):
            machine_key = game.get("machine")
            machine_name = machine_names.get(machine_key, machine_key) if machine_key else None
            thresholds = percentile_data.get(machine_key, []) if machine_key else []

            scores = []
            for i in range(1, num_players + 1):
                raw_score = game.get(f"score_{i}")
                raw_points = game.get(f"points_{i}")
                pct = _score_percentile(raw_score, thresholds) if raw_score and thresholds else None

                player_key = game.get(f"player_{i}")
                player_entry = lineup_lookup.get(player_key, {}) if player_key else {}
                player_name = player_entry.get("name") or player_key

                # Accumulate player points
                if player_key and raw_points is not None:
                    player_points[player_key] = player_points.get(player_key, 0.0) + float(
                        raw_points
                    )

                scores.append(
                    LiveScore(
                        score=raw_score,
                        points=raw_points,
                        percentile=pct,
                        player_key=player_key,
                        player_name=player_name,
                    )
                )

            games.append(
                LiveGame(
                    n=game.get("n", 0),
                    machine_key=machine_key,
                    machine_name=machine_name,
                    scores=scores,
                    away_points=game.get("away_points"),
                    home_points=game.get("home_points"),
                )
            )

        # left_confirmed / right_confirmed can be a dict (with "by"/"at") or bool
        left_conf = rd.get("left_confirmed")
        right_conf = rd.get("right_confirmed")
        rounds.append(
            LiveRound(
                n=n,
                games=games,
                done=bool(rd.get("done", False)),
                left_confirmed=bool(left_conf),
                right_confirmed=bool(right_conf),
            )
        )

    away_lineup = _build_roster(raw, "away", player_points)
    home_lineup = _build_roster(raw, "home", player_points)

    summary = _build_summary(db_match, raw)
    return LiveMatchDetail(
        **summary.model_dump(),
        rounds=rounds,
        away_lineup=away_lineup,
        home_lineup=home_lineup,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/week",
    response_model=LiveWeekResponse,
    summary="Get live match status for the current week",
    description=(
        "Fetches all matches for the current (or specified) week from "
        "mondaynightpinball.com in parallel and returns their live state and "
        "running point totals. Results cached for 60 seconds."
    ),
)
async def get_live_week(
    season: int = Query(default=CURRENT_SEASON, description="Season number"),
    week: int | None = Query(None, description="Week number (defaults to most recent played week)"),
    refresh: bool = Query(False, description="Bypass the 60-second cache"),
):
    if week is None:
        week = _get_current_week(season)

    cache_key = f"{season}:{week}"
    now = datetime.utcnow()

    if not refresh and cache_key in _week_cache:
        cached = _week_cache[cache_key]
        if cached["expires"] > now:
            return cached["data"]

    db_matches = _get_week_matches_from_db(season, week)
    if not db_matches:
        raise HTTPException(
            status_code=404,
            detail=f"No matches found for season {season} week {week}",
        )

    # Fetch all matches from the main site in parallel
    raw_results = await asyncio.gather(*[_fetch_match_json(m["match_key"]) for m in db_matches])

    summaries = [_build_summary(db_match, raw) for db_match, raw in zip(db_matches, raw_results)]

    result = LiveWeekResponse(season=season, week=week, matches=summaries)
    _week_cache[cache_key] = {"data": result, "expires": now + WEEK_TTL}
    return result


@router.get(
    "/matches/{match_key}",
    response_model=LiveMatchDetail,
    summary="Get live match detail with percentile overlays",
    description=(
        "Fetches a single match from mondaynightpinball.com and enriches each "
        "game score with its historical percentile rank on that machine. "
        "Active matches cached for 30s; complete matches cached for 10 minutes."
    ),
)
async def get_live_match(
    match_key: str,
    refresh: bool = Query(False, description="Bypass the cache"),
):
    now = datetime.utcnow()

    if not refresh and match_key in _match_cache:
        cached = _match_cache[match_key]
        if cached["expires"] > now:
            return cached["data"]

    # Get team names and date from our DB
    db_rows = execute_query(
        """
        SELECT
            m.match_key, m.week, m.date,
            m.away_team_key, t1.team_name AS away_team_name,
            m.home_team_key, t2.team_name AS home_team_name,
            m.venue_key
        FROM matches m
        LEFT JOIN teams t1 ON t1.team_key = m.away_team_key AND t1.season = m.season
        LEFT JOIN teams t2 ON t2.team_key = m.home_team_key AND t2.season = m.season
        WHERE m.match_key = :match_key
        LIMIT 1
        """,
        {"match_key": match_key},
    )
    if not db_rows:
        raise HTTPException(
            status_code=404,
            detail=f"Match '{match_key}' not found in the database",
        )
    db_match = db_rows[0]

    raw = await _fetch_match_json(match_key)
    if raw is None:
        # Return minimal detail with UNAVAILABLE state instead of 502
        summary = _build_summary(db_match, None)
        detail = LiveMatchDetail(
            **summary.model_dump(),
            rounds=[],
            away_lineup=[],
            home_lineup=[],
        )
        _match_cache[match_key] = {"data": detail, "expires": now + ACTIVE_TTL}
        return detail

    # Collect unique machine keys for batch lookups
    machine_keys = list(
        {
            game.get("machine")
            for rd in raw.get("rounds", [])
            for game in rd.get("games", [])
            if game.get("machine")
        }
    )

    machine_names = _get_machine_names(machine_keys)
    percentile_data = _get_percentile_thresholds(machine_keys)

    detail = _build_detail(db_match, raw, machine_names, percentile_data)

    ttl = COMPLETE_TTL if _parse_state(raw) == "COMPLETE" else ACTIVE_TTL
    _match_cache[match_key] = {"data": detail, "expires": now + ttl}
    return detail
