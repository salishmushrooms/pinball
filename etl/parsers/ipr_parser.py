"""
Parser for IPR.csv file.
Extracts player IPR (Individual Player Rating) data from the canonical IPR CSV file.
"""

import csv
import logging
import hashlib
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class IPRParser:
    """Parse IPR.csv file to extract player ratings"""

    def __init__(self):
        self.ipr_data = {}

    def normalize_player_name(self, name: str) -> str:
        """
        Normalize player name for consistent matching.
        This should match the normalization used in match files.
        """
        return name.strip()

    def generate_player_key(self, name: str) -> str:
        """
        Generate a player key from name using SHA1 hash.
        This matches the player_key generation in match files.
        """
        normalized = self.normalize_player_name(name)
        return hashlib.sha1(normalized.encode('utf-8')).hexdigest()

    def load_ipr_csv(self, file_path: Path) -> Dict[str, int]:
        """
        Load IPR data from CSV file.

        Args:
            file_path: Path to IPR.csv file

        Returns:
            Dictionary mapping player names to IPR values
        """
        ipr_data = {}
        errors = []

        if not file_path.exists():
            logger.error(f"IPR file not found: {file_path}")
            return ipr_data

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    ipr = int(row['IPR'])
                    name = self.normalize_player_name(row['Name'])

                    # Validate IPR is in range 1-6
                    if ipr < 1 or ipr > 6:
                        errors.append(f"{name}: {ipr}")
                        logger.warning(f"Skipping invalid IPR value for {name}: {ipr} (must be 1-6)")
                        continue  # Skip this player - don't update their IPR

                    ipr_data[name] = ipr

            logger.info(f"Loaded IPR data for {len(ipr_data)} players from {file_path}")
            if errors:
                logger.warning(f"Skipped {len(errors)} players with invalid IPR values (must be 1-6):")
                for error in errors[:10]:  # Show first 10
                    logger.warning(f"  - {error}")
                if len(errors) > 10:
                    logger.warning(f"  ... and {len(errors) - 10} more")

        except Exception as e:
            logger.error(f"Error loading IPR file {file_path}: {e}")
            raise

        return ipr_data

    def extract_ipr_updates(self, file_path: Path) -> List[Dict]:
        """
        Extract IPR data as a list of player updates.

        Args:
            file_path: Path to IPR.csv file

        Returns:
            List of dictionaries with player_name and current_ipr
        """
        ipr_data = self.load_ipr_csv(file_path)

        updates = []
        for name, ipr in ipr_data.items():
            updates.append({
                'player_name': name,
                'current_ipr': ipr
            })

        return updates

    def get_ipr_by_name(self, name: str) -> int:
        """
        Get IPR for a specific player by name.

        Args:
            name: Player name

        Returns:
            IPR value or None if not found
        """
        normalized_name = self.normalize_player_name(name)
        return self.ipr_data.get(normalized_name)
