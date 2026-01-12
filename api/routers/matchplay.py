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
from datetime import datetime, timedelta

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
    description="Get rating, IFPA data, and machine statistics from Matchplay for a linked player"
)
async def get_player_matchplay_stats(
    player_key: str,
    refresh: bool = Query(False, description="Force refresh all data from Matchplay API (profile and machine stats)")
):
    """
    Get Matchplay statistics for a linked MNP player.

    Returns:
    - Rating (value, deviation, game count, win/loss record)
    - IFPA data (rank, rating)
    - Tournament count
    - Machine statistics (games played, wins, win % per machine)

    Note: Profile data (rating, IFPA) is cached for 24 hours. Machine statistics
    are cached until manually refreshed. Use refresh=true to force update all data.
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

    # Check if we have cached profile data that's less than 24 hours old
    rating = None
    ifpa = None
    location = None
    avatar = None
    tournament_count = None
    cache_stale = True

    cached_profile_query = """
        SELECT rating_value, rating_rd, game_count, win_count, loss_count,
               efficiency_percent, lower_bound, ifpa_id, ifpa_rank, ifpa_rating,
               ifpa_womens_rank, tournament_count, location, avatar, fetched_at
        FROM matchplay_ratings
        WHERE matchplay_user_id = :matchplay_user_id
        ORDER BY fetched_at DESC
        LIMIT 1
    """
    cached_profile = execute_query(cached_profile_query, {'matchplay_user_id': matchplay_user_id})

    if cached_profile and not refresh:
        cached = cached_profile[0]
        fetched_at = cached.get('fetched_at')
        if fetched_at and datetime.utcnow() - fetched_at < timedelta(hours=24):
            cache_stale = False
            logger.debug(f"Using cached profile data for player {player_key} (fetched {fetched_at})")

            # Use cached data
            location = cached.get('location')
            avatar = cached.get('avatar')
            tournament_count = cached.get('tournament_count')

            if cached.get('rating_value') is not None:
                rating = MatchplayRating(
                    rating=float(cached['rating_value']) if cached['rating_value'] else None,
                    rd=float(cached['rating_rd']) if cached['rating_rd'] else None,
                    game_count=cached.get('game_count'),
                    win_count=cached.get('win_count'),
                    loss_count=cached.get('loss_count'),
                    efficiency_percent=float(cached['efficiency_percent']) if cached['efficiency_percent'] else None,
                    lower_bound=float(cached['lower_bound']) if cached['lower_bound'] else None,
                    fetched_at=fetched_at
                )

            if cached.get('ifpa_id') is not None or cached.get('ifpa_rank') is not None:
                ifpa = MatchplayIFPA(
                    ifpa_id=cached.get('ifpa_id'),
                    rank=cached.get('ifpa_rank'),
                    rating=float(cached['ifpa_rating']) if cached['ifpa_rating'] else None,
                    womens_rank=cached.get('ifpa_womens_rank')
                )

    # Fetch fresh profile data if cache is stale (> 24 hours) or missing
    if cache_stale and client.is_configured():
        try:
            logger.info(f"Fetching fresh profile data for player {player_key} (cache stale or missing)")
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

                # Cache the profile data in database
                with get_db_connection() as conn:
                    # Delete old cached rating for this user
                    conn.execute(text("""
                        DELETE FROM matchplay_ratings
                        WHERE matchplay_user_id = :matchplay_user_id
                    """), {'matchplay_user_id': matchplay_user_id})

                    # Insert new cached profile data
                    conn.execute(text("""
                        INSERT INTO matchplay_ratings
                            (matchplay_user_id, rating_value, rating_rd, game_count, win_count,
                             loss_count, efficiency_percent, lower_bound, ifpa_id, ifpa_rank,
                             ifpa_rating, ifpa_womens_rank, tournament_count, location, avatar, fetched_at)
                        VALUES
                            (:matchplay_user_id, :rating_value, :rating_rd, :game_count, :win_count,
                             :loss_count, :efficiency_percent, :lower_bound, :ifpa_id, :ifpa_rank,
                             :ifpa_rating, :ifpa_womens_rank, :tournament_count, :location, :avatar, :fetched_at)
                    """), {
                        'matchplay_user_id': matchplay_user_id,
                        'rating_value': rating_data.get('rating') if rating_data else None,
                        'rating_rd': rating_data.get('rd') if rating_data else None,
                        'game_count': rating_data.get('gameCount') if rating_data else None,
                        'win_count': rating_data.get('winCount') if rating_data else None,
                        'loss_count': rating_data.get('lossCount') if rating_data else None,
                        'efficiency_percent': rating_data.get('efficiencyPercent') if rating_data else None,
                        'lower_bound': rating_data.get('lowerBound') if rating_data else None,
                        'ifpa_id': ifpa_data.get('ifpaId') if ifpa_data else None,
                        'ifpa_rank': ifpa_data.get('rank') if ifpa_data else None,
                        'ifpa_rating': ifpa_data.get('rating') if ifpa_data else None,
                        'ifpa_womens_rank': ifpa_data.get('womensRank') if ifpa_data else None,
                        'tournament_count': tournament_count,
                        'location': location,
                        'avatar': avatar,
                        'fetched_at': datetime.utcnow()
                    })

                    # Update last_synced in mappings table
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
    description="Batch lookup of Matchplay ratings for linked players (efficient for rosters). Returns cached ratings by default."
)
async def get_players_matchplay_ratings(
    player_keys: str = Query(..., description="Comma-separated list of player keys"),
    refresh: bool = Query(False, description="Force refresh ratings from Matchplay API (rate-limited)")
):
    """
    Get Matchplay ratings for multiple linked players at once.

    Returns a map of player_key -> rating info for all linked players.
    Players that are not linked will be omitted from the response.

    By default, returns cached ratings from the database for fast loading.
    Use refresh=true to fetch fresh ratings from Matchplay API (rate-limited).

    Example: `/matchplay/players/ratings?player_keys=abc123,def456,ghi789`
    Example: `/matchplay/players/ratings?player_keys=abc123&refresh=true`
    """
    keys = [k.strip() for k in player_keys.split(',') if k.strip()]

    if not keys:
        return {"ratings": {}, "cached": True, "last_updated": None}

    # Batch lookup all linked players with their cached ratings
    placeholders = ', '.join([f':key_{i}' for i in range(len(keys))])
    params = {f'key_{i}': k for i, k in enumerate(keys)}

    # Join with matchplay_ratings to get cached rating data
    mapping_query = f"""
        SELECT
            m.mnp_player_key,
            m.matchplay_user_id,
            m.matchplay_name,
            m.last_synced,
            r.rating_value,
            r.rating_rd,
            r.fetched_at as rating_fetched_at
        FROM matchplay_player_mappings m
        LEFT JOIN matchplay_ratings r ON m.matchplay_user_id = r.matchplay_user_id
        WHERE m.mnp_player_key IN ({placeholders})
    """
    mappings = execute_query(mapping_query, params)

    if not mappings:
        return {"ratings": {}, "cached": True, "last_updated": None}

    client = MatchplayClient()
    ratings = {}
    oldest_fetch = None

    for mapping in mappings:
        player_key = mapping['mnp_player_key']
        matchplay_user_id = mapping['matchplay_user_id']
        matchplay_name = mapping['matchplay_name']
        cached_rating = mapping.get('rating_value')
        cached_rd = mapping.get('rating_rd')
        rating_fetched_at = mapping.get('rating_fetched_at')

        # Track oldest fetch time for cache staleness indication
        if rating_fetched_at and (oldest_fetch is None or rating_fetched_at < oldest_fetch):
            oldest_fetch = rating_fetched_at

        ratings[player_key] = {
            "matchplay_user_id": matchplay_user_id,
            "matchplay_name": matchplay_name,
            "rating": float(cached_rating) if cached_rating is not None else None,
            "rd": float(cached_rd) if cached_rd is not None else None,
            "profile_url": f"https://app.matchplay.events/users/{matchplay_user_id}"
        }

    # If refresh requested and API is configured, fetch fresh ratings
    if refresh and client.is_configured():
        logger.info(f"Refreshing Matchplay ratings for {len(mappings)} players")

        for mapping in mappings:
            player_key = mapping['mnp_player_key']
            matchplay_user_id = mapping['matchplay_user_id']

            # Check rate limit before each call
            if client.rate_limit_remaining is not None and client.rate_limit_remaining <= 2:
                logger.warning("Rate limit nearly exhausted, stopping refresh")
                break

            try:
                profile = await client.get_user_profile(matchplay_user_id)
                if profile:
                    rating_data = profile.get('rating')
                    if rating_data:
                        new_rating = rating_data.get('rating')
                        new_rd = rating_data.get('rd')

                        # Update the response
                        ratings[player_key]["rating"] = new_rating
                        ratings[player_key]["rd"] = new_rd
                        ratings[player_key]["game_count"] = rating_data.get('gameCount')

                        # Store in cache - upsert into matchplay_ratings
                        with get_db_connection() as conn:
                            # Delete existing rating for this user
                            conn.execute(text("""
                                DELETE FROM matchplay_ratings
                                WHERE matchplay_user_id = :matchplay_user_id
                            """), {'matchplay_user_id': matchplay_user_id})

                            # Insert new rating
                            conn.execute(text("""
                                INSERT INTO matchplay_ratings
                                    (matchplay_user_id, rating_value, rating_rd, fetched_at)
                                VALUES
                                    (:matchplay_user_id, :rating_value, :rating_rd, :fetched_at)
                            """), {
                                'matchplay_user_id': matchplay_user_id,
                                'rating_value': new_rating,
                                'rating_rd': new_rd,
                                'fetched_at': datetime.utcnow()
                            })

                            # Update last_synced on mapping
                            conn.execute(text("""
                                UPDATE matchplay_player_mappings
                                SET last_synced = :last_synced
                                WHERE matchplay_user_id = :matchplay_user_id
                            """), {
                                'matchplay_user_id': matchplay_user_id,
                                'last_synced': datetime.utcnow()
                            })
                            conn.commit()

            except Exception as e:
                logger.warning(f"Failed to fetch rating for {player_key}: {e}")

        oldest_fetch = datetime.utcnow()

    return {
        "ratings": ratings,
        "cached": not refresh,
        "last_updated": oldest_fetch.isoformat() if oldest_fetch else None
    }


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


@router.get(
    "/search/users",
    summary="Search Matchplay users",
    description="Open search for Matchplay users by name. Useful for finding players when automatic matching fails."
)
async def search_matchplay_users(
    query: str = Query(..., min_length=2, description="Search query (name)"),
    location_filter: Optional[str] = Query(None, description="Filter results by location substring (e.g., 'Washington', 'WA')")
):
    """
    Search Matchplay.events for users by name.

    This is an open search endpoint that allows searching with any query string,
    useful when the automatic name-based matching doesn't find the right player.

    Optionally filter results to only show users whose location contains the
    specified string (case-insensitive).

    Example: `/matchplay/search/users?query=John&location_filter=Washington`
    """
    client = MatchplayClient()
    if not client.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Matchplay integration not configured. Set MATCHPLAY_API_TOKEN environment variable."
        )

    try:
        # Search Matchplay
        users = await client.search_users(query)

        # Convert to response format
        results = []
        for user_data in users:
            user = MatchplayUser(
                userId=user_data.get('userId') or user_data.get('id'),
                name=user_data.get('name', ''),
                ifpaId=user_data.get('ifpaId'),
                location=user_data.get('location'),
                avatar=user_data.get('avatar')
            )

            # Apply location filter if specified
            if location_filter:
                user_location = user.location or ''
                if location_filter.lower() not in user_location.lower():
                    continue

            results.append(user)

        return {
            "query": query,
            "location_filter": location_filter,
            "total_results": len(results),
            "users": results
        }

    except MatchplayClientError as e:
        logger.error(f"Matchplay API error searching for '{query}': {e}")
        raise HTTPException(status_code=503, detail=f"Matchplay API error: {str(e)}")
