# MNP Data Update Strategy

**Last Updated:** 2025-11-26
**Purpose:** Guide for updating database when new match data becomes available

---

## 📋 Overview

This document outlines the strategy for updating the MNP database during an active season (ongoing) and when adding historical seasons (complete).

### Two Update Scenarios

1. **Active Season Updates** - Weekly updates during a 10-14 week season as new match data arrives
2. **Historical Season Loading** - One-time backfill of complete seasons (18-21)

---

## 🔄 Data Pipeline Order

The ETL pipeline has **dependencies** - some steps must happen before others:

```
1. Load Raw Data (matches, scores, venues, etc.)
   ↓
2. Calculate Percentiles (requires scores to exist)
   ↓
3. Calculate Player Machine Stats (requires percentiles to exist)
```

**Critical:** You **cannot** calculate player stats before percentiles, because player stats include percentile rankings!

---

## 📊 Active Season Updates (During Season)

### When to Update

- **Frequency:** Weekly (after Monday night matches)
- **Timing:** Tuesday morning after all match data is verified
- **Duration:** ~5-10 minutes for Season 22 data

### Update Commands

```bash
# 1. Activate environment
conda activate mnp
cd /Users/JJC/Pinball/MNP

# 2. Load new match data for the current season
python etl/load_season.py --season 22

# This will:
# - Load new matches from mnp-data-archive/season-22/matches/
# - Skip existing matches (based on match_key)
# - Add new scores, games, players, teams

# 3. Recalculate percentiles for current season
python etl/calculate_percentiles.py --season 22

# This will:
# - Delete existing percentiles for season 22
# - Recalculate based on ALL scores (old + new)
# - Takes ~15 seconds

# 4. Recalculate player stats for current season
python etl/calculate_player_stats.py --season 22

# This will:
# - Delete existing player stats for season 22
# - Recalculate aggregations including new percentiles
# - Takes ~30-45 seconds
```

### Is Weekly Recalculation Practical?

**Yes!** ✅ Here's why:

| Step | Time | Why Fast |
|------|------|----------|
| Load matches | ~10-20s | Only loads NEW matches (skips duplicates) |
| Calculate percentiles | ~15s | Only 1 season, ~140 machines |
| Calculate player stats | ~30-45s | Only 1 season, ~6,000 records |
| **Total** | **~1-2 min** | Fully automated, no manual steps |

**Performance:**
- Season 22 has ~11,000 scores → percentiles in 15s
- Season 22 has ~6,000 player×machine combos → stats in 45s
- **Total update time: < 2 minutes per week**

### Automation Potential

You could easily automate this with a simple script:

```bash
#!/bin/bash
# update_current_season.sh

SEASON=22

echo "Starting Season $SEASON update..."
conda activate mnp

echo "1. Loading new matches..."
python etl/load_season.py --season $SEASON

echo "2. Recalculating percentiles..."
python etl/calculate_percentiles.py --season $SEASON

echo "3. Recalculating player stats..."
python etl/calculate_player_stats.py --season $SEASON

echo "✓ Season $SEASON updated successfully!"
```

Run this every Tuesday morning:
```bash
chmod +x update_current_season.sh
./update_current_season.sh
```

---

## 🗃️ Historical Season Loading (One-Time)

### Full Season Backfill

When adding a complete historical season (e.g., Season 23 after it's done):

```bash
SEASON=23

# 1. Load all match data
python etl/load_season.py --season $SEASON

# 2. Calculate percentiles
python etl/calculate_percentiles.py --season $SEASON

# 3. Calculate player stats
python etl/calculate_player_stats.py --season $SEASON
```

### Batch Loading Multiple Seasons

If you need to reload all seasons (e.g., after schema changes):

```bash
#!/bin/bash
# backfill_all_seasons.sh

for SEASON in 18 19 20 21 22; do
  echo "Processing Season $SEASON..."

  python etl/load_season.py --season $SEASON
  python etl/calculate_percentiles.py --season $SEASON
  python etl/calculate_player_stats.py --season $SEASON

  echo "✓ Season $SEASON complete"
done

echo "✓ All seasons processed!"
```

**Time estimate:** ~2 minutes per season × 5 seasons = ~10 minutes total

---

## 📁 Data Files Location

### Source Data (Read-Only)
```
mnp-data-archive/
├── season-18/matches/*.json    # Historical matches
├── season-19/matches/*.json
├── season-20/matches/*.json
├── season-21/matches/*.json
├── season-22/matches/*.json    # Current season (growing weekly)
├── machines.json               # Machine variations
├── venues.json                 # Venue information
└── IPR.csv                     # Player IPR ratings
```

### Database (Updated by ETL)
```
PostgreSQL Database: mnp_analyzer
├── matches                     # Match metadata
├── scores                      # Individual scores (56,504 total)
├── score_percentiles           # Percentile thresholds per machine/season
├── player_machine_stats        # Aggregated player stats (~31,000 total)
└── Other tables...
```

---

## 🎯 Current Data Status

### Loaded Seasons

| Season | Matches | Scores | Percentiles | Player Stats | Status |
|--------|---------|--------|-------------|--------------|--------|
| 18 | ~190 | ~11,300 | ✅ 163 machines | ✅ 6,379 records | Complete |
| 19 | ~190 | ~11,300 | ✅ 151 machines | ✅ 6,278 records | Complete |
| 20 | ~190 | ~11,400 | ✅ 157 machines | ✅ 6,360 records | Complete |
| 21 | ~190 | ~11,340 | ✅ 154 machines | ✅ 6,129 records | Complete |
| 22 | ~180 | ~11,000 | ✅ 140 machines | ✅ 5,942 records | In Progress |

**Total:** 943 matches, 56,504 scores, ~31,088 player stats

---

## ⚙️ Update Strategy Recommendations

### For Ongoing Season (Season 22+)

**Option 1: Manual Weekly Updates** (Recommended for now)
- Run 3 commands every Tuesday morning
- Takes < 2 minutes
- Simple, predictable, reliable

**Option 2: Automated Updates**
- Create a cron job or scheduled task
- Runs `update_current_season.sh` automatically
- Requires monitoring/alerting for failures

**Option 3: On-Demand via Web Interface** (Future)
- Add "Update Data" button to frontend
- Triggers ETL pipeline via API
- Shows progress/status to user

### For New Seasons

When Season 23 starts:
1. Update `update_current_season.sh` to use `SEASON=23`
2. Run the full pipeline once to initialize
3. Continue weekly updates

When Season 23 ends:
- The data is already loaded!
- No backfill needed
- Just update scripts to `SEASON=24` for next season

---

## 🚨 Important Notes

### Percentile Dependencies

**Player stats MUST be recalculated after percentiles!**

Why? Because `player_machine_stats` includes:
- `median_percentile` - Calculated from `score_percentiles` table
- `avg_percentile` - Calculated from `score_percentiles` table

If you calculate player stats before percentiles:
- Percentile fields will be `NULL`
- Frontend will show "N/A" for percentiles

**Correct Order:**
```bash
# ✅ CORRECT
python etl/calculate_percentiles.py --season 22
python etl/calculate_player_stats.py --season 22

# ❌ WRONG
python etl/calculate_player_stats.py --season 22
python etl/calculate_percentiles.py --season 22  # Too late!
```

### Data Deletion Strategy

All ETL scripts use **delete and replace** strategy:

```python
# Before inserting new data
DELETE FROM score_percentiles WHERE season = 22;
DELETE FROM player_machine_stats WHERE season = 22;
```

This means:
- ✅ No duplicate data
- ✅ Old stats are replaced with fresh calculations
- ✅ Safe to run multiple times
- ⚠️ Each season is independent (no cross-season impact)

### Performance Considerations

Current performance (Season 22, ~11,000 scores):
- Percentiles: ~15 seconds
- Player stats: ~45 seconds

Projected performance (Season with 15,000 scores):
- Percentiles: ~20 seconds
- Player stats: ~60 seconds

**Conclusion:** Weekly recalculation is very practical! 🚀

---

## 📝 Quick Reference Commands

### Check What's Loaded
```bash
# Connect to database
psql -U mnp_user -d mnp_analyzer

# Count records by season
SELECT season, COUNT(*) as match_count
FROM matches
GROUP BY season
ORDER BY season DESC;

SELECT season, COUNT(*) as score_count
FROM scores
GROUP BY season
ORDER BY season DESC;

SELECT season, COUNT(*) as percentile_count
FROM score_percentiles
GROUP BY season
ORDER BY season DESC;

SELECT season, COUNT(*) as player_stat_count
FROM player_machine_stats
GROUP BY season
ORDER BY season DESC;
```

### Verify Data Quality
```bash
# Check for NULL percentiles (should be 0 after proper load)
SELECT COUNT(*)
FROM player_machine_stats
WHERE season = 22
  AND median_percentile IS NULL;

# Check percentile coverage
SELECT
  s.season,
  COUNT(DISTINCT s.machine_key) as machines_with_scores,
  COUNT(DISTINCT p.machine_key) as machines_with_percentiles
FROM scores s
LEFT JOIN score_percentiles p ON s.machine_key = p.machine_key AND s.season = p.season
WHERE s.season = 22
GROUP BY s.season;
```

---

## 🎓 Lessons Learned

1. **Always calculate percentiles before player stats**
   - Learned this the hard way when seasons 18-21 showed "N/A"
   - Fixed by running percentiles first, then recalculating player stats

2. **Weekly recalculation is fast enough**
   - < 2 minutes for full season update
   - No need for incremental/delta updates

3. **Delete and replace is simple and reliable**
   - No complex merge logic
   - No duplicate detection needed
   - Just wipe season data and recalculate

4. **Performance scales well**
   - ~15 seconds for 11,000 scores
   - Even 20,000 scores would be < 30 seconds

---

## 🔮 Future Enhancements

### Near-Term
- Create `update_current_season.sh` automation script
- Add verification checks after each update
- Log update history to database table

### Long-Term
- Web UI for triggering updates
- Email/Slack notifications when update completes
- Automatic backup before updates
- Delta detection (only recalculate changed machines)

---

**Last Season Updated:** Season 22 (Week 11 of 14)
**Next Update Due:** After Week 12 matches (check Tuesday morning)
**Estimated Time:** < 2 minutes
