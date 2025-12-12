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
        SELECT id, mnp_player_key, matchplay_user_id, matchplay_name, ifpa_id, match_method, created_at, last_synced
        FROM matchplay_player_mappings
        WHERE mnp_player_key = :player_key OR matchplay_user_id = :matchplay_user_id
    """
    existing = execute_query(existing_query, {
        'player_key': player_key,
        'matchplay_user_id': request.matchplay_user_id
    })

    if existing:
        row = existing[0]
        # Check if this is the EXACT same link being requested (idempotent case)
        if row['mnp_player_key'] == player_key and row['matchplay_user_id'] == request.matchplay_user_id:
            # Return success - link already exists with same mapping
            logger.info(f"Link already exists for MNP player '{player_key}' to Matchplay user {request.matchplay_user_id}")
            mapping = MatchplayPlayerMapping(
                id=row['id'],
                mnp_player_key=row['mnp_player_key'],
                matchplay_user_id=row['matchplay_user_id'],
                matchplay_name=row['matchplay_name'],
                ifpa_id=row['ifpa_id'],
                match_method=row['match_method'],
                created_at=row['created_at'],
                last_synced=row['last_synced']
            )
            return MatchplayLinkResponse(status="already_linked", mapping=mapping)
        else:
            # Conflict: Either player is linked to different matchplay user,
            # or matchplay user is linked to different player
            raise HTTPException(
                status_code=409,
                detail="Player or Matchplay user is already linked to a different account"
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

    Note: This endpoint is idempotent - calling it when no link exists
    returns success (already_unlinked) rather than 404 to handle race conditions
    gracefully.
    """
    # Use a single transaction with DELETE ... RETURNING to atomically
    # check existence and delete in one operation (prevents race conditions)
    with get_db_connection() as conn:
        # First, try to delete and get the matchplay_user_id in one atomic operation
        result = conn.execute(text("""
            DELETE FROM matchplay_player_mappings
            WHERE mnp_player_key = :player_key
            RETURNING matchplay_user_id
        """), {'player_key': player_key})

        deleted_row = result.fetchone()

        if deleted_row:
            matchplay_user_id = deleted_row[0]

            # Delete related cached data (cascade should handle this, but be explicit)
            # These may already be gone due to ON DELETE CASCADE, which is fine
            conn.execute(text("""
                DELETE FROM matchplay_player_machine_stats
                WHERE matchplay_user_id = :matchplay_user_id
            """), {'matchplay_user_id': matchplay_user_id})

            conn.execute(text("""
                DELETE FROM matchplay_ratings
                WHERE matchplay_user_id = :matchplay_user_id
            """), {'matchplay_user_id': matchplay_user_id})

            conn.commit()
            logger.info(f"Unlinked MNP player '{player_key}' from Matchplay user {matchplay_user_id}")
            return {"status": "unlinked", "player_key": player_key}
        else:
            # No link existed - this is fine, return success (idempotent)
            # This handles race conditions where two unlink requests arrive simultaneously
            conn.rollback()
            logger.info(f"Unlink called for MNP player '{player_key}' but no link existed (already unlinked)")
            return {"status": "already_unlinked", "player_key": player_key}


@router.get(
    "/player/{player_key}/stats",
    response_model=MatchplayPlayerStats,
    responses={404: {"model": ErrorResponse}},
    summary="Get Matchplay stats for linked player",
    description="Get rating, IFPA data, and statistics from Matchplay for a linked player"
)
async def get_player_matchplay_stats(
    player_key: str,
    refresh: bool = Query(False, description="Force refresh from Matchplay API")
):
    """
    Get Matchplay statistics for a linked MNP player.

    Returns:
    - Rating (value, deviation, game count, win/loss record)
    - IFPA data (rank, rating)
    - Tournament count
    - Machine statistics (if cached)

    Use refresh=true to force fetching fresh data from Matchplay API.
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

    # Get cached machine stats
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
    client = MatchplayClient()
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
        # Note: rate_limit_remaining is None until first API call, so allow that case
        if client.is_configured() and (client.rate_limit_remaining is None or client.rate_limit_remaining > 2):
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
