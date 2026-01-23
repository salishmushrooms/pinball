-- Migration 006: Add per-match machines column
--
-- This migration adds a JSONB column to store the machines available at
-- the venue for each specific match. This enables accurate opportunity
-- calculation, as venues can change their machine lineup mid-season.
--
-- Previously, opportunities were calculated using venue_machines table
-- which stores machines at venue+season level, losing per-match detail.

-- Add machines JSONB column to matches table
ALTER TABLE matches ADD COLUMN IF NOT EXISTS machines JSONB;

-- Add comment documenting the column
COMMENT ON COLUMN matches.machines IS
    'Array of machine keys available at venue for this specific match (from match JSON venue.machines)';

-- Create GIN index for efficient querying of machines array
CREATE INDEX IF NOT EXISTS idx_matches_machines
ON matches USING GIN (machines);
