-- Matchplay.events Integration Migration
-- Version: 1.0.7
-- Created: 2025-12-01
-- Description: Add tables for Matchplay.events player mapping and cached data

-- ============================================================================
-- MATCHPLAY PLAYER MAPPINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS matchplay_player_mappings (
    id SERIAL PRIMARY KEY,
    mnp_player_key VARCHAR(64) NOT NULL UNIQUE,
    matchplay_user_id INTEGER NOT NULL UNIQUE,
    matchplay_name VARCHAR(255),
    ifpa_id INTEGER,
    match_method VARCHAR(20) DEFAULT 'manual',  -- 'auto' (100% name match), 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP,
    CONSTRAINT fk_mnp_player FOREIGN KEY (mnp_player_key) REFERENCES players(player_key)
);

COMMENT ON TABLE matchplay_player_mappings IS 'Maps MNP players to Matchplay.events user profiles';
COMMENT ON COLUMN matchplay_player_mappings.mnp_player_key IS 'MNP player key (references players table)';
COMMENT ON COLUMN matchplay_player_mappings.matchplay_user_id IS 'Matchplay.events userId';
COMMENT ON COLUMN matchplay_player_mappings.matchplay_name IS 'Name as it appears on Matchplay';
COMMENT ON COLUMN matchplay_player_mappings.ifpa_id IS 'IFPA player ID if available';
COMMENT ON COLUMN matchplay_player_mappings.match_method IS 'How the match was made: auto (100% name match) or manual';
COMMENT ON COLUMN matchplay_player_mappings.last_synced IS 'When data was last fetched from Matchplay API';

CREATE INDEX IF NOT EXISTS idx_mp_mappings_mnp ON matchplay_player_mappings(mnp_player_key);
CREATE INDEX IF NOT EXISTS idx_mp_mappings_mp_user ON matchplay_player_mappings(matchplay_user_id);

-- ============================================================================
-- MATCHPLAY RATINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS matchplay_ratings (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL,
    rating_value DECIMAL(8,2),
    rating_rd DECIMAL(6,2),  -- Rating deviation (uncertainty)
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mp_rating_user FOREIGN KEY (matchplay_user_id)
        REFERENCES matchplay_player_mappings(matchplay_user_id) ON DELETE CASCADE
);

COMMENT ON TABLE matchplay_ratings IS 'Cached Matchplay ratings for linked players';
COMMENT ON COLUMN matchplay_ratings.rating_value IS 'Matchplay rating value';
COMMENT ON COLUMN matchplay_ratings.rating_rd IS 'Rating deviation (lower = more certain)';

CREATE INDEX IF NOT EXISTS idx_mp_ratings_user ON matchplay_ratings(matchplay_user_id);
CREATE INDEX IF NOT EXISTS idx_mp_ratings_fetched ON matchplay_ratings(fetched_at DESC);

-- ============================================================================
-- MATCHPLAY PLAYER MACHINE STATS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS matchplay_player_machine_stats (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL,
    machine_key VARCHAR(50),  -- Mapped to our machine_key if possible, NULL if no mapping
    matchplay_arena_name VARCHAR(255) NOT NULL,  -- Original name from Matchplay
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_percentage DECIMAL(5,2),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mp_machine_stats_user FOREIGN KEY (matchplay_user_id)
        REFERENCES matchplay_player_mappings(matchplay_user_id) ON DELETE CASCADE,
    CONSTRAINT fk_mp_machine_stats_machine FOREIGN KEY (machine_key)
        REFERENCES machines(machine_key) ON DELETE SET NULL,
    UNIQUE(matchplay_user_id, matchplay_arena_name)
);

COMMENT ON TABLE matchplay_player_machine_stats IS 'Cached machine statistics from Matchplay for linked players';
COMMENT ON COLUMN matchplay_player_machine_stats.machine_key IS 'MNP machine key if mapped, NULL otherwise';
COMMENT ON COLUMN matchplay_player_machine_stats.matchplay_arena_name IS 'Machine/arena name as it appears in Matchplay';
COMMENT ON COLUMN matchplay_player_machine_stats.games_played IS 'Number of games played on this machine in Matchplay';
COMMENT ON COLUMN matchplay_player_machine_stats.wins IS 'Number of wins on this machine';
COMMENT ON COLUMN matchplay_player_machine_stats.win_percentage IS 'Calculated win percentage (0-100)';

CREATE INDEX IF NOT EXISTS idx_mp_machine_stats_user ON matchplay_player_machine_stats(matchplay_user_id);
CREATE INDEX IF NOT EXISTS idx_mp_machine_stats_machine ON matchplay_player_machine_stats(machine_key);

-- ============================================================================
-- MATCHPLAY ARENA MAPPINGS TABLE (for machine name normalization)
-- ============================================================================

CREATE TABLE IF NOT EXISTS matchplay_arena_mappings (
    matchplay_arena_name VARCHAR(255) PRIMARY KEY,
    machine_key VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_arena_mapping_machine FOREIGN KEY (machine_key)
        REFERENCES machines(machine_key) ON DELETE SET NULL
);

COMMENT ON TABLE matchplay_arena_mappings IS 'Maps Matchplay arena names to MNP machine keys';
COMMENT ON COLUMN matchplay_arena_mappings.matchplay_arena_name IS 'Arena/machine name as it appears in Matchplay (e.g., "Medieval Madness (Williams, 1997)")';
COMMENT ON COLUMN matchplay_arena_mappings.machine_key IS 'Corresponding MNP machine key (e.g., "MM")';

CREATE INDEX IF NOT EXISTS idx_arena_mappings_machine ON matchplay_arena_mappings(machine_key);

-- ============================================================================
-- UPDATE SCHEMA VERSION
-- ============================================================================

INSERT INTO schema_version (version, description)
VALUES ('1.0.7', 'Add Matchplay.events integration tables')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 007_matchplay_integration.sql completed successfully!';
    RAISE NOTICE 'Added tables: matchplay_player_mappings, matchplay_ratings, matchplay_player_machine_stats, matchplay_arena_mappings';
END $$;
