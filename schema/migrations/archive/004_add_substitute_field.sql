-- Migration: Add is_substitute field to scores table
-- Version: 1.1.0
-- Created: 2025-11-30
-- Description: Track substitute players to allow filtering roster vs non-roster players

-- Add is_substitute column to scores table
ALTER TABLE scores ADD COLUMN is_substitute BOOLEAN DEFAULT false;

COMMENT ON COLUMN scores.is_substitute IS 'True if player was a substitute (not on official roster)';

-- Update schema version
INSERT INTO schema_version (version, description) VALUES
    ('1.1.0', 'Added is_substitute field to scores table');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 004 applied successfully!';
    RAISE NOTICE 'Added is_substitute column to scores table';
END $$;
