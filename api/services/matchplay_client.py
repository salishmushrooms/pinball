"""
Matchplay.events API client for fetching player and tournament data.

API Documentation: https://app.matchplay.events/api-docs/
"""
import os
import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


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
        Get games for a specific player.

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
