"""
Service to match MNP players with Matchplay.events profiles.

Matching strategy:
- 100% exact name match (case-insensitive) -> auto-link eligible
- Any other match -> requires manual confirmation
"""
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional
import logging

from api.services.matchplay_client import MatchplayClient

logger = logging.getLogger(__name__)


class PlayerMatcher:
    """
    Matches MNP players to Matchplay.events profiles by name.
    """

    def __init__(self, client: Optional[MatchplayClient] = None):
        """
        Initialize the player matcher.

        Args:
            client: Optional MatchplayClient instance. If not provided, creates a new one.
        """
        self.client = client or MatchplayClient()

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for comparison."""
        return name.lower().strip()

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity ratio between two names.

        Args:
            name1: First name
            name2: Second name

        Returns:
            Similarity ratio between 0.0 and 1.0
        """
        return SequenceMatcher(
            None,
            self._normalize_name(name1),
            self._normalize_name(name2)
        ).ratio()

    def _is_exact_match(self, mnp_name: str, matchplay_name: str) -> bool:
        """
        Check if two names are an exact match (case-insensitive).

        Args:
            mnp_name: Name from MNP
            matchplay_name: Name from Matchplay

        Returns:
            True if names match exactly (ignoring case and whitespace)
        """
        return self._normalize_name(mnp_name) == self._normalize_name(matchplay_name)

    async def find_matches(
        self,
        mnp_name: str,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search Matchplay for players matching the MNP name.

        Args:
            mnp_name: Player name from MNP database
            min_similarity: Minimum similarity score to include in results (0.0-1.0)

        Returns:
            List of match dictionaries sorted by confidence (highest first):
            [
                {
                    "user": { matchplay user object },
                    "confidence": 0.95,
                    "auto_link_eligible": True/False
                },
                ...
            ]
        """
        # Search Matchplay for the name
        try:
            results = await self.client.search_users(mnp_name)
        except Exception as e:
            logger.error(f"Error searching Matchplay for '{mnp_name}': {e}")
            return []

        if not results:
            logger.debug(f"No Matchplay results for '{mnp_name}'")
            return []

        # Score each result
        matches = []
        for user in results:
            mp_name = user.get("name", "")
            if not mp_name:
                continue

            is_exact = self._is_exact_match(mnp_name, mp_name)
            confidence = 1.0 if is_exact else self._calculate_similarity(mnp_name, mp_name)

            # Only include if above minimum threshold
            if confidence >= min_similarity:
                matches.append({
                    "user": user,
                    "confidence": round(confidence, 4),
                    "auto_link_eligible": is_exact
                })

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        logger.debug(
            f"Found {len(matches)} potential matches for '{mnp_name}' "
            f"(exact matches: {sum(1 for m in matches if m['auto_link_eligible'])})"
        )

        return matches

    async def find_best_match(self, mnp_name: str) -> Optional[Dict[str, Any]]:
        """
        Find the single best match for an MNP player.

        Args:
            mnp_name: Player name from MNP database

        Returns:
            Best match dictionary or None if no good match found
        """
        matches = await self.find_matches(mnp_name)
        return matches[0] if matches else None

    async def batch_find_matches(
        self,
        mnp_names: List[str],
        auto_link_only: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find matches for multiple MNP players.

        Args:
            mnp_names: List of MNP player names
            auto_link_only: If True, only return exact (auto-link eligible) matches

        Returns:
            Dictionary mapping MNP names to their match results
        """
        results = {}

        for name in mnp_names:
            matches = await self.find_matches(name)

            if auto_link_only:
                matches = [m for m in matches if m["auto_link_eligible"]]

            results[name] = matches

        return results
