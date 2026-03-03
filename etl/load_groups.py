#!/usr/bin/env python3
"""
Load team group/division assignments from groups.csv into teams.division column.

groups.csv format: division_letter,division_name,team_key1,team_key2,...
Example: P,Plunger,KNR,SSS,ETB,RTR,LAS,DTP,DSV,ICB,HHS

Usage:
    python etl/load_groups.py --season 23
"""

import argparse
import csv
import logging
import sys

from sqlalchemy import text

from etl.config import config
from etl.database import db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def load_groups(season: int) -> bool:
    groups_path = config.get_season_path(season) / "groups.csv"

    if not groups_path.exists():
        logger.error(f"groups.csv not found at {groups_path}")
        return False

    # Parse: division_letter, division_name, team_key1, team_key2, ...
    assignments: list[tuple[str, str, str]] = []
    with open(groups_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue
            division_letter, division_name = row[0].strip(), row[1].strip()
            for team_key in row[2:]:
                team_key = team_key.strip()
                if team_key:
                    assignments.append((team_key, division_letter, division_name))

    logger.info(f"Found {len(assignments)} team-group assignments in groups.csv")

    updated = 0
    not_found = []
    with db.engine.begin() as conn:
        for team_key, division_letter, division_name in assignments:
            result = conn.execute(
                text("""
                    UPDATE teams
                    SET division = :division
                    WHERE team_key = :team_key AND season = :season
                """),
                {
                    "division": f"{division_letter} - {division_name}",
                    "team_key": team_key,
                    "season": season,
                },
            )
            if result.rowcount > 0:
                updated += 1
                logger.debug(f"  {team_key} → Group {division_letter} ({division_name})")
            else:
                not_found.append(team_key)

    logger.info(f"✓ Updated division for {updated} teams in season {season}")
    if not_found:
        logger.warning(f"  Teams not found in DB: {', '.join(not_found)}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Load team group assignments from groups.csv")
    parser.add_argument("--season", type=int, required=True, help="Season number (e.g., 23)")
    args = parser.parse_args()

    try:
        db.connect()
        success = load_groups(args.season)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
