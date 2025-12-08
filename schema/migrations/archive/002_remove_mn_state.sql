-- Migration to remove MN state references
-- Version: 2.0.0
-- Created: 2025-11-26
-- Description: Remove MN/Minnesota location data (MNP = Monday Night Pinball, not Minnesota Pinball)

-- Remove the DEFAULT constraint from state column
ALTER TABLE venues ALTER COLUMN state DROP DEFAULT;

-- Update all existing venues to have NULL state instead of 'MN'
UPDATE venues SET state = NULL WHERE state = 'MN';

-- Update schema version
INSERT INTO schema_version (version, description) VALUES
    ('2.0.0', 'Removed MN state references from venues table');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: Removed MN state references';
    RAISE NOTICE 'All venues with state=MN have been updated to NULL';
END $$;
