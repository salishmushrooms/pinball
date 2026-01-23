-- Migration 005: Add opportunity tracking to team_machine_picks
--
-- This migration adds columns to track:
-- 1. total_opportunities - How many times a team could have picked this machine
--    (based on matches where the machine was available at the venue)
-- 2. wilson_lower - Wilson score lower bound for confidence-weighted ranking
--    (prevents 1/1 = 100% from ranking higher than 7/10 = 70%)

-- Add total_opportunities column
ALTER TABLE team_machine_picks
ADD COLUMN IF NOT EXISTS total_opportunities INTEGER DEFAULT 0;

-- Add wilson_lower column for pre-computed confidence weighting
ALTER TABLE team_machine_picks
ADD COLUMN IF NOT EXISTS wilson_lower DECIMAL(5,4) DEFAULT 0;

-- Add comments documenting the columns
COMMENT ON COLUMN team_machine_picks.total_opportunities IS
    'Number of matches where team could pick this machine (machine was available at venue)';

COMMENT ON COLUMN team_machine_picks.wilson_lower IS
    'Wilson score lower bound (95% CI) for pick rate - used for confidence-weighted sorting';

-- Create index for efficient querying by wilson_lower
CREATE INDEX IF NOT EXISTS idx_team_machine_picks_wilson
ON team_machine_picks(season, round_type, wilson_lower DESC);
