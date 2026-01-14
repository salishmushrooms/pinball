-- Add missing columns that code expects but production DB doesn't have
-- Version: 2.0.1
-- Created: 2026-01-14
-- Description: Sync production schema with code expectations

-- ============================================================================
-- MATCHPLAY_RATINGS TABLE - Add missing columns
-- ============================================================================

ALTER TABLE matchplay_ratings
    ADD COLUMN IF NOT EXISTS game_count INTEGER,
    ADD COLUMN IF NOT EXISTS win_count INTEGER,
    ADD COLUMN IF NOT EXISTS loss_count INTEGER,
    ADD COLUMN IF NOT EXISTS efficiency_percent DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS lower_bound DECIMAL(8,2),
    ADD COLUMN IF NOT EXISTS ifpa_id INTEGER,
    ADD COLUMN IF NOT EXISTS ifpa_rank INTEGER,
    ADD COLUMN IF NOT EXISTS ifpa_rating DECIMAL(8,2),
    ADD COLUMN IF NOT EXISTS ifpa_womens_rank INTEGER,
    ADD COLUMN IF NOT EXISTS tournament_count INTEGER,
    ADD COLUMN IF NOT EXISTS location VARCHAR(255),
    ADD COLUMN IF NOT EXISTS avatar TEXT;

COMMENT ON COLUMN matchplay_ratings.game_count IS 'Total games played on Matchplay';
COMMENT ON COLUMN matchplay_ratings.win_count IS 'Total wins on Matchplay';
COMMENT ON COLUMN matchplay_ratings.loss_count IS 'Total losses on Matchplay';
COMMENT ON COLUMN matchplay_ratings.efficiency_percent IS 'Win efficiency percentage';
COMMENT ON COLUMN matchplay_ratings.lower_bound IS 'Lower bound rating estimate';
COMMENT ON COLUMN matchplay_ratings.ifpa_id IS 'IFPA player ID';
COMMENT ON COLUMN matchplay_ratings.ifpa_rank IS 'IFPA world ranking';
COMMENT ON COLUMN matchplay_ratings.ifpa_rating IS 'IFPA rating value';
COMMENT ON COLUMN matchplay_ratings.ifpa_womens_rank IS 'IFPA womens ranking';
COMMENT ON COLUMN matchplay_ratings.tournament_count IS 'Number of tournaments played';
COMMENT ON COLUMN matchplay_ratings.location IS 'Player location from Matchplay profile';
COMMENT ON COLUMN matchplay_ratings.avatar IS 'Avatar URL from Matchplay profile';

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, description)
VALUES ('2.0.1', 'Add missing matchplay_ratings columns for profile caching')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 003_add_missing_columns.sql completed successfully!';
    RAISE NOTICE 'Added columns to matchplay_ratings: game_count, win_count, loss_count, efficiency_percent, lower_bound, ifpa_id, ifpa_rank, ifpa_rating, ifpa_womens_rank, tournament_count, location, avatar';
END $$;
