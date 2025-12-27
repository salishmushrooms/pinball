"""
Matchplay.events integration endpoints.

Provides endpoints for:
- Looking up MNP players on Matchplay.events
- Linking/unlinking player profiles
- Fetching Matchplay stats for linked players
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import logging
from datetime import datetime

from api.models.schemas import (
    MatchplayLookupResult,
    MatchplayMatch,
    MatchplayUser,
    MatchplayPlayerMapping,
    MatchplayLinkRequest,
    MatchplayLinkResponse,
    MatchplayPlayerStats,
    MatchplayRating,
    MatchplayIFPA,
    MatchplayMachineStat,
    ErrorResponse
)
from api.services.matchplay_client import MatchplayClient, MatchplayClientError
from api.services.player_matcher import PlayerMatcher
from api.dependencies import execute_query
from etl.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matchplay", tags=["matchplay"])


def get_db_connection():
    """Get database connection, ensuring it's initialized."""
    if not db.engine:
        db.connect()
    return db.engine.connect()


@router.get(
    "/status",
    summary="Check Matchplay integration status",
    description="Check if Matchplay API is configured and accessible"
)
async def get_matchplay_status():
    """
    Check if the Matchplay.events integration is properly configured.
    """
    client = MatchplayClient()

    status = {
        "configured": client.is_configured(),
        "message": "Matchplay API token is configured" if client.is_configured()
                   else "MATCHPLAY_API_TOKEN environment variable not set"
    }

    # If configured, try a simple API call to verify connectivity
    if client.is_configured():
        try:
            # Search for a common term to test API connectivity
            await client.search_users("test")
            status["api_accessible"] = True
            status["rate_limit_remaining"] = client.rate_limit_remaining
            status["rate_limit_total"] = client.rate_limit_total
        except MatchplayClientError as e:
            status["api_accessible"] = False
            status["error"] = str(e)

    return status


@router.get(
    "/player/{player_key}/lookup",
    response_model=MatchplayLookupResult,
    responses={404: {"model": ErrorResponse}},
    summary="Look up MNP player on Matchplay",
    description="Search Matchplay.events for profiles matching an MNP player's name"
)
async def lookup_player_on_matchplay(player_key: str):
    """
    Look up an MNP player on Matchplay.events.

    Returns potential matches ranked by confidence. Only 100% exact name matches
    are eligible for automatic linking; others require manual confirmation.

    Example: `/matchplay/player/abc123def/lookup`
    """
    # Check if already linked
    existing_query = """
        SELECT id, mnp_player_key, matchplay_user_id, matchplay_name,
               ifpa_id, match_method, created_at, last_synced
        FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key
    """
    existing = execute_query(existing_query, {'player_key': player_key})

    if existing:
        mapping_data = existing[0]
        return MatchplayLookupResult(
            mnp_player={"key": player_key, "name": mapping_data.get('matchplay_name', '')},
            matches=[],
            status="already_linked",
            mapping=MatchplayPlayerMapping(**mapping_data)
        )

    # Get MNP player
    player_query = "SELECT player_key, name FROM players WHERE player_key = :player_key"
    players = execute_query(player_query, {'player_key': player_key})

    if not players:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    player = players[0]
    mnp_name = player['name']

    # Check if Matchplay client is configured
    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured. Set MATCHPLAY_API_TOKEN environment variable."
        )

    # Search Matchplay
    matcher = PlayerMatcher(client)
    try:
        matches = await matcher.find_matches(mnp_name)
    except MatchplayClientError as e:
        logger.error(f"Matchplay API error searching for '{mnp_name}': {e}")
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")

    # Convert to response format
    match_results = []
    for match in matches:
        user_data = match['user']
        match_results.append(MatchplayMatch(
            user=MatchplayUser(
                userId=user_data.get('userId') or user_data.get('id'),
                name=user_data.get('name', ''),
                ifpaId=user_data.get('ifpaId'),
                location=user_data.get('location'),
                avatar=user_data.get('avatar')
            ),
            confidence=match['confidence'],
            auto_link_eligible=match['auto_link_eligible']
        ))

    status = "found" if match_results else "not_found"

    return MatchplayLookupResult(
        mnp_player={"key": player_key, "name": mnp_name},
        matches=match_results,
        status=status,
        mapping=None
    )


@router.post(
    "/player/{player_key}/link",
    response_model=MatchplayLinkResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse}
    },
    summary="Link MNP player to Matchplay profile",
    description="Create a link between an MNP player and a Matchplay.events user"
)
async def link_player_to_matchplay(player_key: str, request: MatchplayLinkRequest):
    """
    Create a verified link between an MNP player and a Matchplay user.

    The matchplay_user_id should come from a previous lookup call.
    Links are marked as 'manual' unless the match was 100% exact.
    """
    # Verify MNP player exists
    player_query = "SELECT player_key, name FROM players WHERE player_key = :player_key"
    players = execute_query(player_query, {'player_key': player_key})

    if not players:
        raise HTTPException(status_code=404, detail=f"Player '{player_key}' not found")

    player = players[0]
    mnp_name = player['name']

    # Check if already linked
    existing_query = """
        SELECT id FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key OR matchplay_user_id = :matchplay_user_id
    """
    existing = execute_query(existing_query, {
        'player_key': player_key,
        'matchplay_user_id': request.matchplay_user_id
    })

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Player or Matchplay user is already linked"
        )

    # Fetch Matchplay user info to store name
    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured"
        )

    try:
        # Try to get user profile for name
        # If that fails, search and find the user
        matchplay_name = None
        ifpa_id = None

        try:
            user_data = await client.get_user_profile(request.matchplay_user_id)
            matchplay_name = user_data.get('name')
            ifpa_id = user_data.get('ifpaId')
        except Exception:
            # If direct profile fetch fails, try searching
            search_results = await client.search_users(mnp_name)
            for result in search_results:
                if result.get('userId') == request.matchplay_user_id or result.get('id') == request.matchplay_user_id:
                    matchplay_name = result.get('name')
                    ifpa_id = result.get('ifpaId')
                    break

        # Determine if this was an exact match (for match_method)
        match_method = 'manual'
        if matchplay_name and matchplay_name.lower().strip() == mnp_name.lower().strip():
            match_method = 'auto'

        # Insert mapping
        insert_query = """
            INSERT INTO matchplay_player_mappings
                (mnp_player_key, matchplay_user_id, matchplay_name, ifpa_id, match_method, created_at)
            VALUES
                (:mnp_player_key, :matchplay_user_id, :matchplay_name, :ifpa_id, :match_method, :created_at)
            RETURNING id, mnp_player_key, matchplay_user_id, matchplay_name, ifpa_id, match_method, created_at, last_synced
        """

        with get_db_connection() as conn:
            result = conn.execute(text(insert_query), {
                'mnp_player_key': player_key,
                'matchplay_user_id': request.matchplay_user_id,
                'matchplay_name': matchplay_name or mnp_name,
                'ifpa_id': ifpa_id,
                'match_method': match_method,
                'created_at': datetime.utcnow()
            })
            conn.commit()
            row = result.fetchone()

            if row:
                mapping = MatchplayPlayerMapping(
                    id=row[0],
                    mnp_player_key=row[1],
                    matchplay_user_id=row[2],
                    matchplay_name=row[3],
                    ifpa_id=row[4],
                    match_method=row[5],
                    created_at=row[6],
                    last_synced=row[7]
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to create mapping")

        logger.info(f"Linked MNP player '{player_key}' to Matchplay user {request.matchplay_user_id}")

        return MatchplayLinkResponse(status="linked", mapping=mapping)

    except MatchplayClientError as e:
        logger.error(f"Matchplay API error: {e}")
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")


@router.delete(
    "/player/{player_key}/link",
    responses={404: {"model": ErrorResponse}},
    summary="Unlink MNP player from Matchplay profile",
    description="Remove the link between an MNP player and Matchplay.events"
)
async def unlink_player_from_matchplay(player_key: str):
    """
    Remove the link between an MNP player and their Matchplay profile.

    This also removes any cached Matchplay data for the player.
    """
    # Check if link exists
    existing_query = """
        SELECT matchplay_user_id FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key
    """
    existing = execute_query(existing_query, {'player_key': player_key})

    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"No Matchplay link found for player '{player_key}'"
        )

    matchplay_user_id = existing[0]['matchplay_user_id']

    # Delete related data (cascade should handle this, but be explicit)
    with get_db_connection() as conn:
        # Delete machine stats
        conn.execute(text("""
            DELETE FROM matchplay_player_machine_stats
            WHERE matchplay_user_id = :matchplay_user_id
        """), {'matchplay_user_id': matchplay_user_id})

        # Delete ratings
        conn.execute(text("""
            DELETE FROM matchplay_ratings
            WHERE matchplay_user_id = :matchplay_user_id
        """), {'matchplay_user_id': matchplay_user_id})

        # Delete mapping
        conn.execute(text("""
            DELETE FROM matchplay_player_mappings
            WHERE mnp_player_key = :player_key
        """), {'player_key': player_key})

        conn.commit()

    logger.info(f"Unlinked MNP player '{player_key}' from Matchplay")

    return {"status": "unlinked", "player_key": player_key}


@router.get(
    "/player/{player_key}/stats",
    response_model=MatchplayPlayerStats,
    responses={404: {"model": ErrorResponse}},
    summary="Get Matchplay stats for linked player",
    description="Get rating, IFPA data, and machine statistics from Matchplay for a linked player"
)
async def get_player_matchplay_stats(
    player_key: str,
    refresh: bool = Query(False, description="Force refresh machine stats from Matchplay API (fetches past 1 year of games)")
):
    """
    Get Matchplay statistics for a linked MNP player.

    Returns:
    - Rating (value, deviation, game count, win/loss record)
    - IFPA data (rank, rating)
    - Tournament count
    - Machine statistics (games played, wins, win % per machine)

    Note: Machine statistics are based on the past 1 year of Matchplay data
    to ensure relevance. Use refresh=true to update cached machine stats.
    """
    # Get mapping
    mapping_query = """
        SELECT id, mnp_player_key, matchplay_user_id, matchplay_name, ifpa_id,
               match_method, created_at, last_synced
        FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key
    """
    mappings = execute_query(mapping_query, {'player_key': player_key})

    if not mappings:
        raise HTTPException(
            status_code=404,
            detail=f"Player '{player_key}' not linked to Matchplay. Use /lookup first."
        )

    mapping = mappings[0]
    matchplay_user_id = mapping['matchplay_user_id']
    matchplay_name = mapping['matchplay_name']

    # Initialize client early - we'll need it for refresh or profile fetch
    client = MatchplayClient()

    # If refresh requested, fetch fresh machine stats from past 1 year
    if refresh and client.is_configured():
        try:
            logger.info(f"Refreshing machine stats for player {player_key} (past 1 year)")
            games = await client.get_all_player_games(matchplay_user_id)

            if games:
                aggregated_stats = client.aggregate_machine_stats(games, matchplay_user_id)

                # Update database
                with get_db_connection() as conn:
                    conn.execute(text("""
                        DELETE FROM matchplay_player_machine_stats
                        WHERE matchplay_user_id = :matchplay_user_id
                    """), {'matchplay_user_id': matchplay_user_id})

                    for arena_name, arena_stats in aggregated_stats.items():
                        conn.execute(text("""
                            INSERT INTO matchplay_player_machine_stats
                                (matchplay_user_id, machine_key, matchplay_arena_name,
                                 games_played, wins, win_percentage, fetched_at)
                            VALUES
                                (:matchplay_user_id, NULL, :arena_name,
                                 :games_played, :wins, :win_percentage, :fetched_at)
                        """), {
                            'matchplay_user_id': matchplay_user_id,
                            'arena_name': arena_name,
                            'games_played': arena_stats['games_played'],
                            'wins': arena_stats['wins'],
                            'win_percentage': arena_stats['win_percentage'],
                            'fetched_at': datetime.utcnow()
                        })
                    conn.commit()

                logger.info(f"Refreshed {len(aggregated_stats)} machines from {len(games)} games")
        except MatchplayClientError as e:
            logger.warning(f"Failed to refresh machine stats: {e}")

    # Get cached machine stats (possibly just refreshed)
    stats_query = """
        SELECT machine_key, matchplay_arena_name, games_played, wins, win_percentage
        FROM matchplay_player_machine_stats
        WHERE matchplay_user_id = :matchplay_user_id
        ORDER BY games_played DESC
    """
    stats = execute_query(stats_query, {'matchplay_user_id': matchplay_user_id})

    machine_stats = [
        MatchplayMachineStat(
            machine_key=s['machine_key'],
            matchplay_arena_name=s['matchplay_arena_name'],
            games_played=s['games_played'],
            wins=s['wins'],
            win_percentage=s['win_percentage']
        )
        for s in stats
    ]

    # Always fetch fresh profile data from API (it's fast and gives us current rating)
    rating = None
    ifpa = None
    location = None
    avatar = None
    tournament_count = None

    if client.is_configured():
        try:
            # Fetch full user profile with rating, IFPA, and counts
            profile_data = await client.get_user_profile(matchplay_user_id)

            if profile_data:
                # Extract user info
                user_info = profile_data.get('user', {})
                location = user_info.get('location')
                avatar = user_info.get('avatar')
                matchplay_name = user_info.get('name') or matchplay_name

                # Extract rating data
                rating_data = profile_data.get('rating')
                if rating_data:
                    rating = MatchplayRating(
                        rating=rating_data.get('rating'),
                        rd=rating_data.get('rd'),
                        game_count=rating_data.get('gameCount'),
                        win_count=rating_data.get('winCount'),
                        loss_count=rating_data.get('lossCount'),
                        efficiency_percent=rating_data.get('efficiencyPercent'),
                        lower_bound=rating_data.get('lowerBound'),
                        fetched_at=datetime.utcnow()
                    )

                # Extract IFPA data
                ifpa_data = profile_data.get('ifpa')
                if ifpa_data:
                    ifpa = MatchplayIFPA(
                        ifpa_id=ifpa_data.get('ifpaId'),
                        rank=ifpa_data.get('rank'),
                        rating=ifpa_data.get('rating'),
                        womens_rank=ifpa_data.get('womensRank')
                    )

                # Extract tournament count
                counts = profile_data.get('userCounts', {})
                tournament_count = counts.get('tournamentPlayCount')

                # Update last_synced in database
                with get_db_connection() as conn:
                    conn.execute(text("""
                        UPDATE matchplay_player_mappings
                        SET last_synced = :last_synced
                        WHERE matchplay_user_id = :matchplay_user_id
                    """), {
                        'matchplay_user_id': matchplay_user_id,
                        'last_synced': datetime.utcnow()
                    })
                    conn.commit()

        except MatchplayClientError as e:
            logger.warning(f"Failed to fetch Matchplay profile: {e}")

    return MatchplayPlayerStats(
        matchplay_user_id=matchplay_user_id,
        matchplay_name=matchplay_name or "",
        location=location,
        avatar=avatar,
        rating=rating,
        ifpa=ifpa,
        tournament_count=tournament_count,
        machine_stats=machine_stats,
        profile_url=f"https://app.matchplay.events/users/{matchplay_user_id}"
    )


@router.get(
    "/search/tournaments",
    summary="Search Matchplay tournaments",
    description="Search for tournaments on Matchplay.events by name"
)
async def search_matchplay_tournaments(
    query: str = Query(..., min_length=2, description="Search query")
):
    """
    Search for tournaments on Matchplay.events.

    Useful for investigating whether MNP matches are uploaded to Matchplay.
    """
    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured"
        )

    try:
        results = await client.search_tournaments(query)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except MatchplayClientError as e:
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")


@router.get(
    "/players/ratings",
    summary="Get Matchplay ratings for multiple players",
    description="Batch lookup of Matchplay ratings for linked players (efficient for rosters)"
)
async def get_players_matchplay_ratings(
    player_keys: str = Query(..., description="Comma-separated list of player keys")
):
    """
    Get Matchplay ratings for multiple linked players at once.

    Returns a map of player_key -> rating info for all linked players.
    Players that are not linked will be omitted from the response.

    Example: `/matchplay/players/ratings?player_keys=abc123,def456,ghi789`
    """
    keys = [k.strip() for k in player_keys.split(',') if k.strip()]

    if not keys:
        return {"ratings": {}}

    # Batch lookup all linked players
    placeholders = ', '.join([f':key_{i}' for i in range(len(keys))])
    params = {f'key_{i}': k for i, k in enumerate(keys)}

    mapping_query = f"""
        SELECT mnp_player_key, matchplay_user_id, matchplay_name
        FROM matchplay_player_mappings
        WHERE mnp_player_key IN ({placeholders})
    """
    mappings = execute_query(mapping_query, params)

    if not mappings:
        return {"ratings": {}}

    # For now, return cached info from mappings
    # If we need fresh ratings, we'd need to batch API calls which is rate-limited
    client = MatchplayClient()
    ratings = {}

    for mapping in mappings:
        player_key = mapping['mnp_player_key']
        matchplay_user_id = mapping['matchplay_user_id']
        matchplay_name = mapping['matchplay_name']

        ratings[player_key] = {
            "matchplay_user_id": matchplay_user_id,
            "matchplay_name": matchplay_name,
            "rating": None,
            "profile_url": f"https://app.matchplay.events/users/{matchplay_user_id}"
        }

        # Try to fetch rating from API (with rate limiting awareness)
        if client.is_configured() and client.rate_limit_remaining and client.rate_limit_remaining > 2:
            try:
                profile = await client.get_user_profile(matchplay_user_id)
                if profile:
                    rating_data = profile.get('rating')
                    if rating_data:
                        ratings[player_key]["rating"] = rating_data.get('rating')
                        ratings[player_key]["rd"] = rating_data.get('rd')
                        ratings[player_key]["game_count"] = rating_data.get('gameCount')
            except Exception as e:
                logger.warning(f"Failed to fetch rating for {player_key}: {e}")

    return {"ratings": ratings}


@router.post(
    "/player/{player_key}/refresh-machine-stats",
    summary="Refresh machine statistics for a linked player",
    description="Fetches game history from Matchplay (past 1 year) and updates cached machine stats"
)
async def refresh_player_machine_stats(player_key: str):
    """
    Refresh machine statistics for a linked player from Matchplay.

    This fetches the player's game history from the past 1 year and aggregates
    their per-machine statistics (games played, wins, win percentage).

    Note: Only games from the past 1 year are included to ensure data relevance.
    Older tournament results are excluded.

    Rate-limited by Matchplay API - use sparingly.
    """
    # Get mapping
    mapping_query = """
        SELECT matchplay_user_id, matchplay_name
        FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key
    """
    mappings = execute_query(mapping_query, {'player_key': player_key})

    if not mappings:
        raise HTTPException(
            status_code=404,
            detail=f"Player '{player_key}' not linked to Matchplay"
        )

    matchplay_user_id = mappings[0]['matchplay_user_id']

    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured"
        )

    try:
        # Fetch all games from past 1 year
        games = await client.get_all_player_games(matchplay_user_id)

        if not games:
            return {
                "status": "success",
                "message": "No games found in the past 1 year",
                "games_processed": 0,
                "machines_updated": 0
            }

        # Aggregate into machine stats
        machine_stats = client.aggregate_machine_stats(games, matchplay_user_id)

        # Update database - delete old stats and insert new ones
        with get_db_connection() as conn:
            # Delete existing stats for this player
            conn.execute(text("""
                DELETE FROM matchplay_player_machine_stats
                WHERE matchplay_user_id = :matchplay_user_id
            """), {'matchplay_user_id': matchplay_user_id})

            # Insert new stats
            for arena_name, stats in machine_stats.items():
                # Try to map arena name to our machine_key
                # For now, we'll leave machine_key as NULL and rely on the arena name
                conn.execute(text("""
                    INSERT INTO matchplay_player_machine_stats
                        (matchplay_user_id, machine_key, matchplay_arena_name,
                         games_played, wins, win_percentage, fetched_at)
                    VALUES
                        (:matchplay_user_id, NULL, :arena_name,
                         :games_played, :wins, :win_percentage, :fetched_at)
                """), {
                    'matchplay_user_id': matchplay_user_id,
                    'arena_name': arena_name,
                    'games_played': stats['games_played'],
                    'wins': stats['wins'],
                    'win_percentage': stats['win_percentage'],
                    'fetched_at': datetime.utcnow()
                })

            # Update last_synced timestamp
            conn.execute(text("""
                UPDATE matchplay_player_mappings
                SET last_synced = :last_synced
                WHERE matchplay_user_id = :matchplay_user_id
            """), {
                'matchplay_user_id': matchplay_user_id,
                'last_synced': datetime.utcnow()
            })

            conn.commit()

        logger.info(f"Refreshed machine stats for player {player_key}: {len(games)} games, {len(machine_stats)} machines")

        return {
            "status": "success",
            "message": f"Updated machine stats from past 1 year of Matchplay data",
            "games_processed": len(games),
            "machines_updated": len(machine_stats),
            "data_window": "past 1 year"
        }

    except MatchplayClientError as e:
        logger.error(f"Matchplay API error refreshing stats: {e}")
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")


@router.get(
    "/investigate/mnp-tournaments",
    summary="Investigate MNP data in Matchplay",
    description="Search for Monday Night Pinball tournaments to check for data duplication"
)
async def investigate_mnp_tournaments():
    """
    Investigate whether Monday Night Pinball data is uploaded to Matchplay.

    This searches for tournaments with MNP-related names to identify potential
    data duplication between our MNP match database and Matchplay statistics.

    If MNP data IS in Matchplay:
    - Machine stats may include MNP match performance (duplication)
    - Consider filtering out MNP tournaments from Matchplay stats

    If MNP data is NOT in Matchplay:
    - Matchplay stats represent external tournament play only
    - No data duplication concerns
    """
    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured"
        )

    search_terms = [
        "Monday Night Pinball",
        "MNP",
        "MNP Seattle",
        "Monday Night"
    ]

    results = {}
    total_found = 0

    try:
        for term in search_terms:
            tournaments = await client.search_tournaments(term)
            results[term] = {
                "count": len(tournaments),
                "tournaments": tournaments[:10]  # Limit to first 10 for brevity
            }
            total_found += len(tournaments)

        # Analyze results
        has_mnp_data = total_found > 0
        analysis = {
            "mnp_data_found": has_mnp_data,
            "total_tournaments_found": total_found,
            "recommendation": (
                "MNP tournaments found in Matchplay. Machine statistics may include "
                "MNP match data, which could cause duplication with our local MNP database. "
                "Consider filtering out MNP tournaments when aggregating Matchplay stats."
                if has_mnp_data else
                "No MNP tournaments found in Matchplay. Machine statistics represent "
                "external tournament play only - no data duplication concerns."
            )
        }

        return {
            "analysis": analysis,
            "search_results": results
        }

    except MatchplayClientError as e:
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")
