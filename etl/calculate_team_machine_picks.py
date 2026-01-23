#!/usr/bin/env python3
"""
Calculate team machine pick statistics and populate team_machine_picks table.

This script analyzes which machines teams choose when they have the pick:
- Home team picks in rounds 2 & 4
- Away team picks in rounds 1 & 3

It tracks:
- times_picked: How many times a team picked this machine
- wins: Number of round wins on this machine
- total_points: Points earned on this machine
- avg_score: Average score on this machine

Usage:
    python etl/calculate_team_machine_picks.py --season 22
    python etl/calculate_team_machine_picks.py --season 22 --verbose
"""

import argparse
import logging
import math
import sys
from collections import defaultdict
from sqlalchemy import text

from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def fetch_games_with_scores(season: int):
    """
    Fetch all games with their scores for a season.

    Uses the scores table directly since it has denormalized machine_key.
    This avoids issues with the game_id linkage which may not be correct
    for all records.

    Returns:
        list: Game records with team performance data
    """
    logger.info(f"Fetching games and scores for season {season}...")

    # Use scores table directly - it has machine_key denormalized
    # This correctly handles multiple machines per round
    # Filter by complete matches to be consistent with opportunities calculation
    query = """
        SELECT
            s.match_key,
            s.round_number,
            s.machine_key,
            m.home_team_key,
            m.away_team_key,
            s.team_key,
            s.is_home_team,
            s.score
        FROM scores s
        JOIN matches m ON s.match_key = m.match_key
        WHERE s.season = :season
        AND m.state = 'complete'
        ORDER BY s.match_key, s.round_number, s.machine_key, s.team_key
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    logger.info(f"Fetched {len(rows)} score records")
    return rows


def determine_picking_team(round_number: int, home_team_key: str, away_team_key: str):
    """
    Determine which team picked the machine for a given round.

    Rules:
    - Home team picks rounds 2 & 4
    - Away team picks rounds 1 & 3

    Returns:
        tuple: (picking_team_key, is_home)
    """
    if round_number in [2, 4]:
        return home_team_key, True
    else:  # rounds 1 & 3
        return away_team_key, False


def get_round_type(round_number: int):
    """
    Get the round type (singles or doubles).

    Rounds 1 & 4 are doubles (4 players)
    Rounds 2 & 3 are singles (2 players)
    """
    if round_number in [1, 4]:
        return 'doubles'
    else:
        return 'singles'


def calculate_wilson_lower(successes: int, total: int, z: float = 1.96) -> float:
    """
    Calculate Wilson score lower bound for 95% confidence interval.

    This is used to rank items by confidence-adjusted rate, preventing
    items with small sample sizes from dominating (e.g., 1/1 = 100%
    won't rank higher than 7/10 = 70%).

    Args:
        successes: Number of successes (times picked)
        total: Total opportunities
        z: Z-score for confidence level (1.96 for 95% CI)

    Returns:
        Lower bound of Wilson score interval (0.0 to 1.0)
    """
    if total == 0:
        return 0.0

    # Handle edge case where successes > total (data inconsistency)
    # This can happen if venue_machines data is incomplete
    if successes > total:
        # Use successes as total since we know they had at least that many opportunities
        total = successes

    p = successes / total
    denominator = 1 + (z * z) / total
    center = p + (z * z) / (2 * total)
    spread = z * math.sqrt((p * (1 - p) / total) + (z * z) / (4 * total * total))
    return (center - spread) / denominator


def calculate_opportunities(season: int) -> dict:
    """
    Calculate pick opportunities for each (team, machine, is_home, round_type).

    An opportunity exists when:
    1. The team had pick rights in that round (home picks 2&4, away picks 1&3)
    2. The machine was available at the venue for that specific match

    Uses per-match machines from matches.machines JSONB column for accuracy,
    with fallback to venue_machines table if per-match data is not available.

    Returns:
        dict: {(team_key, machine_key, is_home, round_type): opportunity_count}
    """
    logger.info(f"Calculating pick opportunities for season {season}...")

    # First, check if we have per-match machine data
    check_query = """
        SELECT COUNT(*) FROM matches
        WHERE season = :season AND state = 'complete' AND machines IS NOT NULL
    """
    with db.engine.connect() as conn:
        result = conn.execute(text(check_query), {'season': season})
        matches_with_machines = result.fetchone()[0]

    if matches_with_machines > 0:
        logger.info(f"Using per-match machine data ({matches_with_machines} matches with data)")
        query = """
            WITH team_match_opportunities AS (
                -- Home team picks Round 4 (doubles)
                SELECT
                    m.home_team_key as team_key,
                    m.match_key,
                    m.machines,
                    true as is_home,
                    'doubles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete' AND m.machines IS NOT NULL

                UNION ALL

                -- Away team picks Round 1 (doubles)
                SELECT
                    m.away_team_key as team_key,
                    m.match_key,
                    m.machines,
                    false as is_home,
                    'doubles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete' AND m.machines IS NOT NULL

                UNION ALL

                -- Home team picks Round 2 (singles)
                SELECT
                    m.home_team_key as team_key,
                    m.match_key,
                    m.machines,
                    true as is_home,
                    'singles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete' AND m.machines IS NOT NULL

                UNION ALL

                -- Away team picks Round 3 (singles)
                SELECT
                    m.away_team_key as team_key,
                    m.match_key,
                    m.machines,
                    false as is_home,
                    'singles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete' AND m.machines IS NOT NULL
            )
            SELECT
                tmo.team_key,
                machine_key,
                tmo.is_home,
                tmo.round_type,
                COUNT(*) as opportunities
            FROM team_match_opportunities tmo,
                 jsonb_array_elements_text(tmo.machines) as machine_key
            GROUP BY tmo.team_key, machine_key, tmo.is_home, tmo.round_type
        """
    else:
        logger.info("No per-match machine data available, falling back to venue_machines table")
        query = """
            WITH team_matches AS (
                -- Home team picks Round 4 (doubles)
                SELECT
                    m.home_team_key as team_key,
                    m.venue_key,
                    m.season,
                    true as is_home,
                    'doubles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete'

                UNION ALL

                -- Away team picks Round 1 (doubles)
                SELECT
                    m.away_team_key as team_key,
                    m.venue_key,
                    m.season,
                    false as is_home,
                    'doubles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete'

                UNION ALL

                -- Home team picks Round 2 (singles)
                SELECT
                    m.home_team_key as team_key,
                    m.venue_key,
                    m.season,
                    true as is_home,
                    'singles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete'

                UNION ALL

                -- Away team picks Round 3 (singles)
                SELECT
                    m.away_team_key as team_key,
                    m.venue_key,
                    m.season,
                    false as is_home,
                    'singles' as round_type
                FROM matches m
                WHERE m.season = :season AND m.state = 'complete'
            )
            SELECT
                tm.team_key,
                vm.machine_key,
                tm.is_home,
                tm.round_type,
                COUNT(*) as opportunities
            FROM team_matches tm
            JOIN venue_machines vm
                ON tm.venue_key = vm.venue_key
                AND tm.season = vm.season
            WHERE vm.active = true
            GROUP BY tm.team_key, vm.machine_key, tm.is_home, tm.round_type
        """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    opportunities = {}
    for row in rows:
        team_key, machine_key, is_home, round_type, count = row
        key = (team_key, machine_key, is_home, round_type)
        opportunities[key] = count

    logger.info(f"Calculated {len(opportunities)} opportunity records")
    return opportunities


def aggregate_team_picks(scores, season: int):
    """
    Aggregate team machine pick statistics.

    Args:
        scores: List of score records
        season: Season number

    Returns:
        dict: Aggregated pick statistics
    """
    logger.info("Aggregating team machine pick statistics...")

    # Group scores by (match_key, round_number, machine_key, team_key)
    # Each round has MULTIPLE games on different machines, so we need machine_key in the key
    # Structure: {(match, round, machine, team): {'scores': [], 'is_home': bool, ...}}
    game_results = defaultdict(lambda: {'scores': [], 'is_home': None})

    for row in scores:
        match_key, round_num, machine_key, home_team, away_team, team_key, is_home, score = row

        # Include machine_key in the grouping to track each game separately
        key = (match_key, round_num, machine_key, team_key)
        game_results[key]['scores'].append(score)
        game_results[key]['machine'] = machine_key
        game_results[key]['is_home'] = is_home
        game_results[key]['home_team'] = home_team
        game_results[key]['away_team'] = away_team
        game_results[key]['round_num'] = round_num

    # Now aggregate by (team, machine, is_home, round_type)
    # Structure: {(team, machine, is_home, round_type): stats}
    pick_stats = defaultdict(lambda: {
        'times_picked': 0,
        'wins': 0,
        'total_points': 0,
        'total_score': 0,
        'game_count': 0
    })

    # Process each game result
    # Each game is uniquely identified by (match_key, round_number, machine_key)
    processed_games = set()

    for (match_key, round_num, machine_key, team_key), data in game_results.items():
        # Game key now includes machine to handle multiple machines per round
        game_key = (match_key, round_num, machine_key)

        # Skip if we've already processed this game
        if game_key in processed_games:
            continue

        home_team = data['home_team']
        away_team = data['away_team']
        machine = data['machine']
        round_type = get_round_type(round_num)

        # Determine who picked this machine
        picking_team, picker_is_home = determine_picking_team(round_num, home_team, away_team)

        # Get scores for both teams in this game (now keyed by machine too)
        home_data = game_results.get((match_key, round_num, machine_key, home_team), {'scores': []})
        away_data = game_results.get((match_key, round_num, machine_key, away_team), {'scores': []})

        home_total = sum(home_data['scores'])
        away_total = sum(away_data['scores'])

        # Calculate points for the picking team
        # In MNP, points are awarded based on head-to-head comparisons
        # For simplicity, we'll track total scores and win/loss
        if picker_is_home:
            picker_total = home_total
            opponent_total = away_total
        else:
            picker_total = away_total
            opponent_total = home_total

        # Determine if the picking team won the round
        won = 1 if picker_total > opponent_total else 0

        # Calculate points (simplified: 1 point for win, 0 for loss)
        # In reality, MNP uses position-based scoring, but this gives a good approximation
        points = won

        # Update stats for the picking team
        stats_key = (picking_team, machine, picker_is_home, round_type)
        pick_stats[stats_key]['times_picked'] += 1
        pick_stats[stats_key]['wins'] += won
        pick_stats[stats_key]['total_points'] += points
        pick_stats[stats_key]['total_score'] += picker_total
        pick_stats[stats_key]['game_count'] += len(home_data['scores']) if picker_is_home else len(away_data['scores'])

        processed_games.add(game_key)

    logger.info(f"Aggregated {len(pick_stats)} team/machine/context combinations")
    return dict(pick_stats)


def clear_existing_picks(season: int):
    """Clear existing team machine picks for the season"""

    logger.info(f"Clearing existing team machine picks for season {season}")

    query = """
        DELETE FROM team_machine_picks
        WHERE season = :season
    """

    with db.engine.begin() as conn:
        conn.execute(text(query), {'season': season})


def insert_team_picks(pick_stats: dict, opportunities: dict, season: int):
    """
    Insert team machine pick statistics into database.

    Args:
        pick_stats: dict of aggregated statistics
        opportunities: dict of pick opportunities per (team, machine, is_home, round_type)
        season: Season number
    """
    logger.info("Inserting team machine pick statistics...")

    query = """
        INSERT INTO team_machine_picks (
            team_key, machine_key, season, is_home, round_type,
            times_picked, wins, total_points, avg_score,
            total_opportunities, wilson_lower
        )
        VALUES (
            :team_key, :machine_key, :season, :is_home, :round_type,
            :times_picked, :wins, :total_points, :avg_score,
            :total_opportunities, :wilson_lower
        )
        ON CONFLICT (team_key, machine_key, season, is_home, round_type)
        DO UPDATE SET
            times_picked = EXCLUDED.times_picked,
            wins = EXCLUDED.wins,
            total_points = EXCLUDED.total_points,
            avg_score = EXCLUDED.avg_score,
            total_opportunities = EXCLUDED.total_opportunities,
            wilson_lower = EXCLUDED.wilson_lower,
            last_calculated = CURRENT_TIMESTAMP
    """

    records_inserted = 0

    with db.engine.begin() as conn:
        for (team_key, machine_key, is_home, round_type), stats in pick_stats.items():
            # Calculate average score
            avg_score = int(stats['total_score'] / stats['game_count']) if stats['game_count'] > 0 else 0

            # Get opportunities for this combination
            opp_key = (team_key, machine_key, is_home, round_type)
            total_opportunities = opportunities.get(opp_key, 0)

            # Warn if picks exceed opportunities (indicates venue_machines data gap)
            if stats['times_picked'] > total_opportunities:
                logger.warning(
                    f"Data inconsistency: {team_key} picked {machine_key} {stats['times_picked']}x "
                    f"but only {total_opportunities} opportunities recorded. "
                    f"Check venue_machines table for missing entries."
                )

            # Calculate Wilson score lower bound
            wilson_lower = calculate_wilson_lower(stats['times_picked'], total_opportunities)

            record = {
                'team_key': team_key,
                'machine_key': machine_key,
                'season': season,
                'is_home': is_home,
                'round_type': round_type,
                'times_picked': stats['times_picked'],
                'wins': stats['wins'],
                'total_points': stats['total_points'],
                'avg_score': avg_score,
                'total_opportunities': total_opportunities,
                'wilson_lower': round(wilson_lower, 4)
            }

            conn.execute(text(query), record)
            records_inserted += 1

    logger.info(f"✓ Inserted {records_inserted} team machine pick records")


def calculate_and_store_team_picks(season: int):
    """
    Main function to calculate and store team machine pick statistics.

    Args:
        season: Season number
    """
    logger.info("=" * 60)
    logger.info(f"Calculating Team Machine Picks for Season {season}")
    logger.info("=" * 60)

    # Step 1: Clear existing data
    clear_existing_picks(season)

    # Step 2: Fetch game and score data
    scores = fetch_games_with_scores(season)

    if not scores:
        logger.error("No scores found!")
        return False

    # Step 3: Aggregate pick statistics
    pick_stats = aggregate_team_picks(scores, season)

    # Step 4: Calculate opportunities (how many times each machine was available to pick)
    opportunities = calculate_opportunities(season)

    # Step 5: Insert into database with opportunities and Wilson scores
    insert_team_picks(pick_stats, opportunities, season)

    logger.info("")
    logger.info("=" * 60)
    logger.info("✓ Team machine picks calculated successfully!")
    logger.info("=" * 60)

    return True


def verify_team_picks(season: int):
    """Verify that team picks were calculated correctly"""

    logger.info("")
    logger.info("Verifying team machine pick statistics...")

    query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT team_key) as unique_teams,
            COUNT(DISTINCT machine_key) as unique_machines,
            SUM(times_picked) as total_picks,
            SUM(wins) as total_wins,
            SUM(total_opportunities) as total_opportunities
        FROM team_machine_picks
        WHERE season = :season
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        row = result.fetchone()

    if row:
        logger.info(f"  Total records: {row[0]}")
        logger.info(f"  Unique teams: {row[1]}")
        logger.info(f"  Unique machines: {row[2]}")
        logger.info(f"  Total picks: {row[3]}")
        logger.info(f"  Total wins: {row[4]}")
        logger.info(f"  Total opportunities: {row[5]}")
        if row[3] and row[3] > 0:
            logger.info(f"  Win rate: {row[4]/row[3]*100:.1f}%")

    # Show top machine picks by Wilson score (confidence-weighted)
    logger.info("")
    logger.info("Top machines by pick rate (doubles, Wilson-weighted):")

    query = """
        SELECT
            machine_key,
            SUM(times_picked) as total_picks,
            SUM(total_opportunities) as total_opps,
            ROUND(SUM(times_picked)::numeric / NULLIF(SUM(total_opportunities), 0) * 100, 1) as pick_rate,
            MAX(wilson_lower) as wilson_score
        FROM team_machine_picks
        WHERE season = :season AND round_type = 'doubles'
        GROUP BY machine_key
        HAVING SUM(total_opportunities) >= 3
        ORDER BY wilson_score DESC
        LIMIT 10
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), {'season': season})
        rows = result.fetchall()

    for row in rows:
        machine, picks, opps, pick_rate, wilson = row
        logger.info(f"  {machine}: {picks}/{opps} picks ({pick_rate}%), wilson={wilson:.3f}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Calculate team machine pick statistics')
    parser.add_argument('--season', type=int, required=True, help='Season number (e.g., 22)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Connect to database
        db.connect()

        # Calculate team picks
        success = calculate_and_store_team_picks(args.season)

        if not success:
            return 1

        # Verify results
        verify_team_picks(args.season)

        logger.info("")
        logger.info("Done!")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
