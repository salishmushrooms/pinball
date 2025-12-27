-- Migration: Replace city/state columns with neighborhood for venues
-- Date: 2025-12-12
-- Description: All MNP venues are in the Seattle area, so city/state is redundant.
--              Neighborhood (e.g., Ballard, Capitol Hill) is more useful.

-- Drop old columns if they exist
ALTER TABLE venues DROP COLUMN IF EXISTS city;
ALTER TABLE venues DROP COLUMN IF EXISTS state;

-- Add neighborhood column if not exists
ALTER TABLE venues ADD COLUMN IF NOT EXISTS neighborhood VARCHAR(100);

-- Add comment
COMMENT ON COLUMN venues.neighborhood IS 'Seattle neighborhood (e.g., Ballard, Capitol Hill)';

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('2.0.0', 'Replace city/state with neighborhood for venues')
ON CONFLICT (version) DO NOTHING;

DO $$
BEGIN
    RAISE NOTICE 'Migration completed: venues table now uses neighborhood instead of city/state';
END $$;
