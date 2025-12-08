-- Migration to allow week 0 for playoff/exhibition matches
-- Version: 1.0.1
-- Created: 2025-11-26
-- Description: Relax week constraint to allow week 0 (playoff matches)

-- Drop the old constraint
ALTER TABLE matches DROP CONSTRAINT matches_week_check;

-- Add new constraint allowing week 0-15
ALTER TABLE matches ADD CONSTRAINT matches_week_check CHECK (week BETWEEN 0 AND 15);

-- Add similar constraint to games table
ALTER TABLE games DROP CONSTRAINT games_round_number_check;
ALTER TABLE games ADD CONSTRAINT games_round_number_check CHECK (round_number BETWEEN 1 AND 4);

-- Update schema version
INSERT INTO schema_version (version, description) VALUES
    ('1.0.1', 'Allow week 0 for playoff/exhibition matches');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 002 applied successfully!';
    RAISE NOTICE 'Week constraint updated to allow 0-15';
END $$;
