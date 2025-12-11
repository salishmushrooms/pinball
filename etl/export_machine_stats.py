#!/usr/bin/env python3
"""
Export machine score statistics for machines with >50 plays.

Generates a JSON file with comprehensive score distribution statistics
for each pinball machine, suitable for LLM consumption.

Usage:
    python etl/export_machine_stats.py
    python etl/export_machine_stats.py --output machine_stats.json
    python etl/export_machine_stats.py --min-plays 100
"""

import argparse
import json
import logging
import sys
from datetime import datetime
import numpy as np
from scipy import stats as scipy_stats
from sqlalchemy import text

from etl.config import config
from etl.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Seasons to include
SEASONS = [20, 21, 22]

# Minimum plays threshold
DEFAULT_MIN_PLAYS = 50


def fetch_machine_scores(seasons: list[int], min_plays: int):
    """
    Fetch all scores grouped by machine for specified seasons.
    Only returns machines with at least min_plays scores.

    Returns:
        dict: {machine_key: {'scores': [...], 'machine_name': str, 'seasons': set}}
    """
    logger.info(f"Fetching scores for seasons {seasons}...")

    season_placeholders = ', '.join([f':season_{i}' for i in range(len(seasons))])
    params = {f'season_{i}': s for i, s in enumerate(seasons)}

    query = f"""
        SELECT
            s.machine_key,
            m.machine_name,
            m.manufacturer,
            m.year,
            s.score,
            s.season
        FROM scores s
        JOIN machines m ON s.machine_key = m.machine_key
        WHERE s.season IN ({season_placeholders})
        ORDER BY s.machine_key, s.score
    """

    with db.engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()

    # Group scores by machine
    machines = {}
    for row in rows:
        machine_key = row[0]

        if machine_key not in machines:
            machines[machine_key] = {
                'machine_name': row[1],
                'manufacturer': row[2],
                'year': row[3],
                'scores': [],
                'seasons': set()
            }

        machines[machine_key]['scores'].append(row[4])
        machines[machine_key]['seasons'].add(row[5])

    # Filter by minimum plays
    filtered = {
        k: v for k, v in machines.items()
        if len(v['scores']) >= min_plays
    }

    logger.info(f"Found {len(filtered)} machines with >= {min_plays} plays")
    return filtered


def calculate_distribution_stats(scores: list[int]) -> dict:
    """
    Calculate comprehensive distribution statistics for a list of scores.

    Returns statistics useful for understanding score distributions:
    - Central tendency: mean, median, mode
    - Spread: std_dev, variance, range, IQR
    - Percentiles: 5th, 10th, 25th, 50th, 75th, 90th, 95th, 99th
    - Shape: skewness, kurtosis
    - Bounds: min, max
    """
    arr = np.array(scores)

    # Calculate percentiles
    percentiles = [5, 10, 25, 50, 75, 90, 95, 99]
    percentile_values = {f'p{p}': int(np.percentile(arr, p)) for p in percentiles}

    # Calculate mode (most common score range - use binned mode for continuous data)
    # Round to nearest 1000 for mode calculation to get meaningful clusters
    if arr.max() > 100000:
        bin_size = 10000
    elif arr.max() > 10000:
        bin_size = 1000
    else:
        bin_size = 100

    binned = (arr // bin_size) * bin_size
    mode_result = scipy_stats.mode(binned, keepdims=True)
    mode_value = int(mode_result.mode[0])
    mode_count = int(mode_result.count[0])

    # Calculate IQR
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1

    # Calculate skewness and kurtosis
    skewness = float(scipy_stats.skew(arr))
    kurtosis = float(scipy_stats.kurtosis(arr))

    stats = {
        # Sample size
        'total_plays': len(scores),

        # Central tendency
        'mean': int(np.mean(arr)),
        'median': int(np.median(arr)),
        'mode_bin': mode_value,
        'mode_bin_size': bin_size,
        'mode_count': mode_count,

        # Spread
        'std_dev': int(np.std(arr)),
        'variance': int(np.var(arr)),
        'range': int(arr.max() - arr.min()),
        'iqr': int(iqr),

        # Bounds
        'min_score': int(arr.min()),
        'max_score': int(arr.max()),

        # Shape (distribution characteristics)
        'skewness': round(skewness, 3),
        'kurtosis': round(kurtosis, 3),

        # Percentiles
        **percentile_values,

        # Coefficient of variation (relative spread)
        'cv': round(np.std(arr) / np.mean(arr), 3) if np.mean(arr) > 0 else 0,
    }

    return stats


def generate_score_interpretation(stats: dict) -> dict:
    """
    Generate human-readable interpretation hints for the statistics.
    """
    interpretation = {}

    # Skewness interpretation
    if stats['skewness'] > 1:
        interpretation['skewness_meaning'] = 'heavily_right_skewed'
        interpretation['skewness_description'] = 'Most scores cluster at lower values with some very high outliers'
    elif stats['skewness'] > 0.5:
        interpretation['skewness_meaning'] = 'moderately_right_skewed'
        interpretation['skewness_description'] = 'Scores tend toward lower values with a tail of higher scores'
    elif stats['skewness'] < -0.5:
        interpretation['skewness_meaning'] = 'left_skewed'
        interpretation['skewness_description'] = 'Scores tend toward higher values'
    else:
        interpretation['skewness_meaning'] = 'approximately_symmetric'
        interpretation['skewness_description'] = 'Scores are relatively evenly distributed around the median'

    # Kurtosis interpretation
    if stats['kurtosis'] > 3:
        interpretation['kurtosis_meaning'] = 'heavy_tailed'
        interpretation['kurtosis_description'] = 'More extreme scores (outliers) than a normal distribution'
    elif stats['kurtosis'] < -1:
        interpretation['kurtosis_meaning'] = 'light_tailed'
        interpretation['kurtosis_description'] = 'Fewer extreme scores than a normal distribution'
    else:
        interpretation['kurtosis_meaning'] = 'normal_tailed'
        interpretation['kurtosis_description'] = 'Similar tail behavior to a normal distribution'

    # Coefficient of variation interpretation
    if stats['cv'] > 1:
        interpretation['variability'] = 'very_high'
        interpretation['variability_description'] = 'Scores vary dramatically; high unpredictability'
    elif stats['cv'] > 0.5:
        interpretation['variability'] = 'high'
        interpretation['variability_description'] = 'Significant score variation between plays'
    elif stats['cv'] > 0.25:
        interpretation['variability'] = 'moderate'
        interpretation['variability_description'] = 'Moderate score variation'
    else:
        interpretation['variability'] = 'low'
        interpretation['variability_description'] = 'Scores are relatively consistent'

    # Score tiers based on percentiles
    interpretation['score_tiers'] = {
        'poor': f'Below {stats["p25"]:,}',
        'below_average': f'{stats["p25"]:,} - {stats["p50"]:,}',
        'above_average': f'{stats["p50"]:,} - {stats["p75"]:,}',
        'good': f'{stats["p75"]:,} - {stats["p90"]:,}',
        'excellent': f'{stats["p90"]:,} - {stats["p95"]:,}',
        'exceptional': f'Above {stats["p95"]:,}'
    }

    return interpretation


def export_machine_stats(output_file: str, min_plays: int):
    """
    Main export function.
    """
    logger.info("=" * 60)
    logger.info("Exporting Machine Score Statistics")
    logger.info(f"Seasons: {SEASONS}")
    logger.info(f"Minimum plays: {min_plays}")
    logger.info("=" * 60)

    # Fetch data
    machines_data = fetch_machine_scores(SEASONS, min_plays)

    if not machines_data:
        logger.error("No machines found matching criteria!")
        return False

    # Build export data
    export_data = {
        'metadata': {
            'description': 'Pinball machine score statistics from Monday Night Pinball league',
            'source': 'MNP (Monday Night Pinball) database',
            'seasons_included': SEASONS,
            'minimum_plays_threshold': min_plays,
            'generated_at': datetime.now().isoformat(),
            'total_machines': len(machines_data),
            'notes': [
                'Scores are from competitive league play (4-player and 2-player rounds)',
                'Statistics represent actual tournament performance, not casual play',
                'Percentiles indicate score thresholds (e.g., p75=500000 means 75% of scores are below 500,000)',
                'Skewness > 0 indicates right-skewed distribution (common in pinball)',
                'CV (coefficient of variation) indicates relative variability'
            ]
        },
        'machines': []
    }

    # Process each machine
    for machine_key, data in sorted(machines_data.items()):
        scores = data['scores']
        stats = calculate_distribution_stats(scores)
        interpretation = generate_score_interpretation(stats)

        machine_entry = {
            'machine_key': machine_key,
            'machine_name': data['machine_name'],
            'manufacturer': data['manufacturer'],
            'year': data['year'],
            'seasons_played': sorted(list(data['seasons'])),
            'statistics': stats,
            'interpretation': interpretation
        }

        export_data['machines'].append(machine_entry)

        logger.info(
            f"  {data['machine_name']}: "
            f"n={stats['total_plays']}, "
            f"median={stats['median']:,}, "
            f"mean={stats['mean']:,}, "
            f"cv={stats['cv']}"
        )

    # Write output file
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"✓ Export complete!")
    logger.info(f"  Output file: {output_file}")
    logger.info(f"  Machines exported: {len(export_data['machines'])}")
    logger.info("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Export machine score statistics for LLM consumption'
    )
    parser.add_argument(
        '--output', '-o',
        default='machine_score_stats.json',
        help='Output file path (default: machine_score_stats.json)'
    )
    parser.add_argument(
        '--min-plays', '-m',
        type=int,
        default=DEFAULT_MIN_PLAYS,
        help=f'Minimum plays threshold (default: {DEFAULT_MIN_PLAYS})'
    )

    args = parser.parse_args()

    try:
        db.connect()
        success = export_machine_stats(args.output, args.min_plays)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
