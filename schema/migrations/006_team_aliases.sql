-- Team Aliases Migration
-- Version: 1.0.6
-- Created: 2025-12-01
-- Description: Add team_aliases table to support team name changes/rebranding
--              Example: Contras (CDC) -> Trolls! (TRL)

-- ============================================================================
-- TEAM ALIASES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS team_aliases (
    alias_key VARCHAR(10) PRIMARY KEY,      -- old team key (e.g., CDC)
    team_key VARCHAR(10) NOT NULL,          -- current team key (e.g., TRL)
    alias_name VARCHAR(255),                -- old team name (e.g., Contras)
    seasons_active TEXT,                    -- comma-separated seasons (e.g., "18,19,20,21")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE team_aliases IS 'Maps historical team keys to current team keys for rebranded teams';
COMMENT ON COLUMN team_aliases.alias_key IS 'Previous team key that should be merged into current team';
COMMENT ON COLUMN team_aliases.team_key IS 'Current/canonical team key';
COMMENT ON COLUMN team_aliases.alias_name IS 'Previous team name for reference';
COMMENT ON COLUMN team_aliases.seasons_active IS 'Seasons when this alias was used (comma-separated)';

-- Index for lookups by current team key
CREATE INDEX IF NOT EXISTS idx_team_aliases_team_key ON team_aliases(team_key);

-- ============================================================================
-- INSERT KNOWN ALIASES
-- ============================================================================

-- Contras (CDC) rebranded to Trolls! (TRL) for season 22
INSERT INTO team_aliases (alias_key, team_key, alias_name, seasons_active)
VALUES ('CDC', 'TRL', 'Contras', '18,19,20,21')
ON CONFLICT (alias_key) DO UPDATE SET
    team_key = EXCLUDED.team_key,
    alias_name = EXCLUDED.alias_name,
    seasons_active = EXCLUDED.seasons_active;

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, description)
VALUES ('1.0.6', 'Add team_aliases table for team rebranding support')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 006_team_aliases.sql completed successfully!';
    RAISE NOTICE 'Added team_aliases table with CDC -> TRL mapping';
END $$;
