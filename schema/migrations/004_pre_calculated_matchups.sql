-- Pre-calculated matchup analysis table
-- Version: 2.1.0
-- Created: 2026-01-21
-- Description: Store pre-computed matchup analysis for faster page loads

-- ============================================================================
-- PRE_CALCULATED_MATCHUPS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS pre_calculated_matchups (
    id SERIAL PRIMARY KEY,

    -- Match identification
    match_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,

    -- Teams and venue (for querying without JSON parsing)
    home_team_key VARCHAR(10) NOT NULL,
    away_team_key VARCHAR(10) NOT NULL,
    venue_key VARCHAR(10) NOT NULL,

    -- Analysis parameters
    seasons_analyzed INTEGER[] NOT NULL,

    -- Full analysis data (MatchupAnalysis JSON structure)
    analysis_data JSONB NOT NULL,

    -- Metadata
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint: one pre-calculation per match
    CONSTRAINT uq_precalc_match_key UNIQUE (match_key)
);

COMMENT ON TABLE pre_calculated_matchups IS 'Pre-computed matchup analysis for scheduled matches';
COMMENT ON COLUMN pre_calculated_matchups.match_key IS 'Match identifier (e.g., mnp-24-5-SKP-TRL)';
COMMENT ON COLUMN pre_calculated_matchups.seasons_analyzed IS 'Seasons included in analysis (e.g., {24, 23})';
COMMENT ON COLUMN pre_calculated_matchups.analysis_data IS 'Full MatchupAnalysis response as JSONB';
COMMENT ON COLUMN pre_calculated_matchups.calculated_at IS 'When this analysis was first calculated';
COMMENT ON COLUMN pre_calculated_matchups.last_calculated IS 'When this analysis was last refreshed';

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_precalc_matchups_season_week
    ON pre_calculated_matchups(season, week);

CREATE INDEX IF NOT EXISTS idx_precalc_matchups_home_team
    ON pre_calculated_matchups(home_team_key, season);

CREATE INDEX IF NOT EXISTS idx_precalc_matchups_away_team
    ON pre_calculated_matchups(away_team_key, season);

CREATE INDEX IF NOT EXISTS idx_precalc_matchups_venue
    ON pre_calculated_matchups(venue_key, season);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

ALTER TABLE pre_calculated_matchups
    DROP CONSTRAINT IF EXISTS fk_precalc_match;

ALTER TABLE pre_calculated_matchups
    ADD CONSTRAINT fk_precalc_match
    FOREIGN KEY (match_key)
    REFERENCES matches(match_key)
    ON DELETE CASCADE;

ALTER TABLE pre_calculated_matchups
    DROP CONSTRAINT IF EXISTS fk_precalc_venue;

ALTER TABLE pre_calculated_matchups
    ADD CONSTRAINT fk_precalc_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE RESTRICT;

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, description)
VALUES ('2.1.0', 'Add pre_calculated_matchups table for faster matchup analysis')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 004_pre_calculated_matchups.sql completed successfully!';
    RAISE NOTICE 'Created table: pre_calculated_matchups';
    RAISE NOTICE 'Created indexes: idx_precalc_matchups_season_week, idx_precalc_matchups_home_team, idx_precalc_matchups_away_team, idx_precalc_matchups_venue';
END $$;
