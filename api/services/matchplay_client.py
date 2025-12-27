"""
Matchplay.events API client for fetching player and tournament data.

API Documentation: https://app.matchplay.events/api-docs/

Note: Machine statistics are filtered to the past 1 year of data to ensure
relevance. Older tournament data is excluded from aggregations.
"""
import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Default lookback period for Matchplay game statistics
MATCHPLAY_DATA_LOOKBACK_DAYS = 365  # 1 year


class MatchplayClientError(Exception):
    """Base exception for Matchplay API errors"""
    pass


class MatchplayRateLimitError(MatchplayClientError):
    """Rate limit exceeded"""
    pass


class MatchplayAuthError(MatchplayClientError):
    """Authentication error"""
    pass


class MatchplayClient:
    """
    Client for interacting with the Matchplay.events API.

    Requires MATCHPLAY_API_TOKEN environment variable to be set.
    """

    BASE_URL = "https://app.matchplay.events"

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Matchplay client.

        Args:
            token: Optional API token. If not provided, reads from MATCHPLAY_API_TOKEN env var.
        """
        self.token = token or os.getenv("MATCHPLAY_API_TOKEN")
        if not self.token:
            logger.warning("MATCHPLAY_API_TOKEN not set - Matchplay integration will not work")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

        # Track rate limits from response headers
        self.rate_limit_remaining: Optional[int] = None
        self.rate_limit_total: Optional[int] = None

    def _update_rate_limits(self, response: httpx.Response) -> None:
        """Update rate limit tracking from response headers."""
        if "x-ratelimit-remaining" in response.headers:
            self.rate_limit_remaining = int(response.headers["x-ratelimit-remaining"])
        if "x-ratelimit-limit" in response.headers:
            self.rate_limit_total = int(response.headers["x-ratelimit-limit"])

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response, checking for errors."""
        self._update_rate_limits(response)

        if response.status_code == 401:
            raise MatchplayAuthError("Invalid or expired API token")

        if response.status_code == 429:
            raise MatchplayRateLimitError("Rate limit exceeded")

        response.raise_for_status()
        return response.json()

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for users by name.

        Args:
            query: Name to search for

        Returns:
            List of user objects matching the query
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/search",
                params={"query": query, "type": "users"},
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", [])

    async def get_user_profile(
        self,
        user_id: int,
        include_ifpa: bool = True,
        include_counts: bool = True
    ) -> Dict[str, Any]:
        """
        Get a user's full profile including rating and IFPA data.

        Args:
            user_id: Matchplay user ID
            include_ifpa: Include IFPA ranking data
            include_counts: Include tournament count data

        Returns:
            Complete user profile with nested rating, ifpa, and userCounts data:
            {
                "user": { userId, name, location, avatar, ... },
                "rating": { rating, rd, gameCount, winCount, lossCount, ... },
                "ifpa": { rank, rating, ... },
                "userCounts": { tournamentPlayCount, ... }
            }
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        params = {}
        if include_ifpa:
            params["includeIfpa"] = 1
        if include_counts:
            params["includeCounts"] = 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/users/{user_id}",
                params=params,
                headers=self.headers
            )
            # This endpoint returns data directly, not nested in "data"
            return self._handle_response(response)

    async def get_rating_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get a user's rating summary.

        Args:
            user_id: Matchplay user ID

        Returns:
            Rating data including:
            - rating: Current rating value
            - rd: Rating deviation (uncertainty)
            - gameCount: Total games played
            - winCount/lossCount: Win/loss record
            - efficiencyPercent: Win percentage
            - lowerBound: Conservative rating estimate
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/ratings/users/{user_id}/summary",
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", {})

    async def get_rating_full(self, user_id: int, rating_type: str = "main") -> Dict[str, Any]:
        """
        Get a user's full rating profile with history.

        Args:
            user_id: Matchplay user ID
            rating_type: Type of rating (default: "main")

        Returns:
            Full rating profile with history
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/ratings/{rating_type}/{user_id}",
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", {})

    async def get_player_games(
        self,
        player_id: int,
        status: Optional[str] = "completed",
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Get games for a specific player (single page).

        Args:
            player_id: Matchplay player/user ID
            status: Filter by status ("started", "completed")
            page: Page number for pagination

        Returns:
            Dict containing games list and pagination info
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        params = {"player": player_id, "page": page}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/games",
                params=params,
                headers=self.headers
            )
            return self._handle_response(response)

    async def get_all_player_games(
        self,
        player_id: int,
        status: Optional[str] = "completed",
        since_days: Optional[int] = MATCHPLAY_DATA_LOOKBACK_DAYS,
        max_pages: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all games for a player, with optional date filtering.

        Note: Fetches games from the past 1 year by default to ensure data relevance.
        Older tournament results are excluded from machine statistics.

        Args:
            player_id: Matchplay player/user ID
            status: Filter by status ("started", "completed")
            since_days: Only include games from the past N days (default: 365 = 1 year)
            max_pages: Maximum pages to fetch (safety limit)

        Returns:
            List of all games matching the criteria
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        # Calculate cutoff date
        cutoff_date = None
        if since_days:
            cutoff_date = datetime.utcnow() - timedelta(days=since_days)
            logger.info(f"Filtering Matchplay games to past {since_days} days (since {cutoff_date.date()})")

        all_games = []
        page = 1
        reached_cutoff = False

        async with httpx.AsyncClient(timeout=30.0) as client:
            while page <= max_pages and not reached_cutoff:
                params = {"player": player_id, "page": page}
                if status:
                    params["status"] = status

                response = await client.get(
                    f"{self.BASE_URL}/api/games",
                    params=params,
                    headers=self.headers
                )
                data = self._handle_response(response)

                games = data.get("data", [])
                if not games:
                    break

                for game in games:
                    # Parse game date - Matchplay uses 'completedAt' or 'createdAt'
                    game_date_str = game.get("completedAt") or game.get("createdAt")
                    if game_date_str and cutoff_date:
                        try:
                            # Handle ISO format with timezone
                            game_date = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
                            game_date = game_date.replace(tzinfo=None)  # Make naive for comparison

                            if game_date < cutoff_date:
                                # Games are ordered by date desc, so we can stop here
                                reached_cutoff = True
                                logger.info(f"Reached date cutoff at page {page}, game date: {game_date.date()}")
                                break
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Could not parse game date '{game_date_str}': {e}")

                    all_games.append(game)

                # Check for next page
                meta = data.get("meta", {})
                current_page = meta.get("currentPage", page)
                last_page = meta.get("lastPage", page)

                if current_page >= last_page:
                    break

                page += 1

        logger.info(f"Fetched {len(all_games)} games for player {player_id} from {page} pages (filtered to past {since_days} days)")
        return all_games

    def aggregate_machine_stats(
        self,
        games: List[Dict[str, Any]],
        player_id: int
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aggregate game data into per-machine statistics.

        Note: This aggregates games that have already been filtered to the past 1 year.

        Args:
            games: List of game objects from Matchplay API
            player_id: The player's Matchplay user ID (to determine wins)

        Returns:
            Dict mapping arena_name -> {games_played, wins, win_percentage}
        """
        stats = {}

        for game in games:
            arena_name = game.get("arenaName") or game.get("arena", {}).get("name")
            if not arena_name:
                continue

            if arena_name not in stats:
                stats[arena_name] = {
                    "arena_name": arena_name,
                    "games_played": 0,
                    "wins": 0
                }

            stats[arena_name]["games_played"] += 1

            # Determine if this player won
            # Winner is determined by position or explicit winner field
            winner_id = game.get("winnerId") or game.get("winner", {}).get("userId")
            if winner_id == player_id:
                stats[arena_name]["wins"] += 1

        # Calculate win percentages
        for arena_name, arena_stats in stats.items():
            if arena_stats["games_played"] > 0:
                arena_stats["win_percentage"] = round(
                    (arena_stats["wins"] / arena_stats["games_played"]) * 100, 2
                )
            else:
                arena_stats["win_percentage"] = 0.0

        return stats

    async def search_tournaments(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for tournaments by name.

        Args:
            query: Tournament name to search for

        Returns:
            List of tournaments matching the query
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/search",
                params={"query": query, "type": "tournaments"},
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", [])

    async def get_tournament(self, tournament_id: int) -> Dict[str, Any]:
        """
        Get tournament details.

        Args:
            tournament_id: Tournament ID

        Returns:
            Tournament data
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/tournaments/{tournament_id}",
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", {})

    async def get_tournament_games(
        self,
        tournament_id: int,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get games from a tournament.

        Args:
            tournament_id: Tournament ID
            status: Optional status filter

        Returns:
            List of games in the tournament
        """
        if not self.token:
            raise MatchplayClientError("API token not configured")

        params = {}
        if status:
            params["status"] = status

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/api/tournaments/{tournament_id}/games",
                params=params,
                headers=self.headers
            )
            data = self._handle_response(response)
            return data.get("data", [])

    def is_configured(self) -> bool:
        """Check if the client has a valid token configured."""
        return bool(self.token)
