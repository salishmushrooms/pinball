"""
Parser for machine_variations.json file.
Extracts canonical machine definitions and aliases.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class MachineParser:
    """Parse machine variations file"""

    def __init__(self, variations_file: Path):
        self.variations_file = variations_file
        self.variations_data = {}
        self.alias_map = {}

    def load(self) -> Dict:
        """Load and parse machine variations file"""
        try:
            with open(self.variations_file, 'r') as f:
                self.variations_data = json.load(f)

            logger.info(f"Loaded {len(self.variations_data)} machines from variations file")
            return self.variations_data

        except FileNotFoundError:
            logger.error(f"Machine variations file not found: {self.variations_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in variations file: {e}")
            raise

    def extract_machines(self) -> List[Dict]:
        """Extract machine definitions for database loading"""
        if not self.variations_data:
            self.load()

        machines = []
        for machine_key, machine_info in self.variations_data.items():
            if isinstance(machine_info, dict):
                # Convert empty strings to None for nullable fields
                manufacturer = machine_info.get('manufacturer')
                year = machine_info.get('year')
                game_type = machine_info.get('type')

                machine = {
                    'machine_key': machine_key,
                    'machine_name': machine_info.get('name', machine_key),
                    'manufacturer': manufacturer if manufacturer else None,
                    'year': year if year else None,
                    'game_type': game_type if game_type else None
                }
                machines.append(machine)

        logger.info(f"Extracted {len(machines)} machine definitions")
        return machines

    def extract_aliases(self) -> List[Dict]:
        """Extract machine aliases for database loading"""
        if not self.variations_data:
            self.load()

        aliases = []
        for machine_key, machine_info in self.variations_data.items():
            if isinstance(machine_info, dict) and 'variations' in machine_info:
                # Add canonical key as alias to itself
                aliases.append({
                    'alias': machine_key,
                    'machine_key': machine_key,
                    'alias_type': 'canonical'
                })

                # Add all variations
                for variation in machine_info['variations']:
                    if variation != machine_key:  # Don't duplicate canonical
                        aliases.append({
                            'alias': variation,
                            'machine_key': machine_key,
                            'alias_type': 'variation'
                        })

        logger.info(f"Extracted {len(aliases)} machine aliases")
        return aliases

    def build_alias_map(self) -> Dict[str, str]:
        """Build mapping from all aliases to canonical machine keys"""
        if not self.variations_data:
            self.load()

        alias_map = {}
        for machine_key, machine_info in self.variations_data.items():
            # Map canonical key to itself
            alias_map[machine_key] = machine_key
            alias_map[machine_key.lower()] = machine_key

            # Map all variations to canonical key
            if isinstance(machine_info, dict) and 'variations' in machine_info:
                for variation in machine_info['variations']:
                    alias_map[variation] = machine_key
                    alias_map[variation.lower()] = machine_key
                    alias_map[variation.strip()] = machine_key

        self.alias_map = alias_map
        logger.info(f"Built alias map with {len(alias_map)} entries")
        return alias_map

    def normalize_machine_key(self, machine_key: str) -> str:
        """Normalize a machine key to its canonical form"""
        if not self.alias_map:
            self.build_alias_map()

        # Clean the input
        cleaned = machine_key.strip()

        # Try exact match first
        if cleaned in self.alias_map:
            return self.alias_map[cleaned]

        # Try case-insensitive match
        if cleaned.lower() in self.alias_map:
            return self.alias_map[cleaned.lower()]

        # Return cleaned key if no match found (log warning)
        logger.warning(f"No canonical key found for: '{machine_key}' - using as-is")
        return cleaned
