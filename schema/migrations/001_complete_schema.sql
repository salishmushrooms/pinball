-- MNP Analyzer Complete Database Schema
-- Version: 2.2.0
-- Created: 2025-12-08
-- Updated: 2026-01-25
-- Description: Consolidated schema with all tables, indexes, and constraints
--
-- This file consolidates all previous migrations:
--   001_initial_schema.sql
--   002_indexes.sql
--   002_allow_week_zero.sql
--   002_remove_mn_state.sql (no longer needed - state has no default)
--   003_constraints.sql
--   004_add_substitute_field.sql
--   005_performance_indexes.sql
--   005_team_machine_picks_opportunities.sql (total_opportunities, wilson_lower columns)
--   006_team_aliases.sql
--   006_match_machines.sql (machines JSONB column on matches)
--   007_matchplay_integration.sql
--   008_scores_unique_constraint.sql (constraint only - dedup not needed for fresh install)

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Players table
CREATE TABLE players (
    player_key VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    current_ipr INTEGER CHECK (current_ipr BETWEEN 1 AND 6),
    first_seen_season INTEGER,
    last_seen_season INTEGER,
    total_games_played INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE players IS 'Player identity and rating information';
COMMENT ON COLUMN players.player_key IS 'SHA-1 hash from MNP system';
COMMENT ON COLUMN players.current_ipr IS 'Individual Player Rating (1-6 scale)';

-- Teams table
CREATE TABLE teams (
    team_key VARCHAR(10) NOT NULL,
    season INTEGER NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    home_venue_key VARCHAR(10),
    division VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_key, season)
);

COMMENT ON TABLE teams IS 'Team information by season';
COMMENT ON COLUMN teams.team_key IS '3-letter team code (e.g., ADB, TBT)';

-- Team aliases table (for team rebranding, e.g., Contras -> Trolls!)
CREATE TABLE team_aliases (
    alias_key VARCHAR(10) PRIMARY KEY,
    team_key VARCHAR(10) NOT NULL,
    alias_name VARCHAR(255),
    seasons_active TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE team_aliases IS 'Maps historical team keys to current team keys for rebranded teams';
COMMENT ON COLUMN team_aliases.alias_key IS 'Previous team key that should be merged into current team';
COMMENT ON COLUMN team_aliases.team_key IS 'Current/canonical team key';
COMMENT ON COLUMN team_aliases.alias_name IS 'Previous team name for reference';
COMMENT ON COLUMN team_aliases.seasons_active IS 'Seasons when this alias was used (comma-separated)';

-- Venues table
CREATE TABLE venues (
    venue_key VARCHAR(10) PRIMARY KEY,
    venue_name VARCHAR(255) NOT NULL,
    address TEXT,
    neighborhood VARCHAR(100),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE venues IS 'Venue information';
COMMENT ON COLUMN venues.venue_key IS '3-4 letter venue code (e.g., T4B, JUP)';
COMMENT ON COLUMN venues.neighborhood IS 'Seattle neighborhood (e.g., Ballard, Capitol Hill)';

-- Machines table
CREATE TABLE machines (
    machine_key VARCHAR(50) PRIMARY KEY,
    machine_name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(100),
    year INTEGER,
    game_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE machines IS 'Canonical machine definitions';
COMMENT ON COLUMN machines.machine_key IS 'Canonical key from machine_variations.json';

-- Machine aliases table
CREATE TABLE machine_aliases (
    alias VARCHAR(100) PRIMARY KEY,
    machine_key VARCHAR(50) NOT NULL,
    alias_type VARCHAR(20)
);

COMMENT ON TABLE machine_aliases IS 'Maps alternate machine names to canonical keys';

-- Venue machines junction table
CREATE TABLE venue_machines (
    venue_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    active BOOLEAN DEFAULT true,
    date_added DATE,
    date_removed DATE,
    PRIMARY KEY (venue_key, machine_key, season)
);

COMMENT ON TABLE venue_machines IS 'Tracks which machines are at which venues by season';

-- Matches table (week 0-15 to support playoffs/exhibition)
CREATE TABLE matches (
    match_key VARCHAR(50) PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 0 AND 15),
    date DATE,
    venue_key VARCHAR(10) NOT NULL,
    home_team_key VARCHAR(10) NOT NULL,
    away_team_key VARCHAR(10) NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    home_team_points INTEGER,
    away_team_points INTEGER,
    machines JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matches IS 'Match metadata';
COMMENT ON COLUMN matches.match_key IS 'Format: mnp-{season}-{week}-{away}-{home}';
COMMENT ON COLUMN matches.state IS 'Match status: scheduled, playing, complete';
COMMENT ON COLUMN matches.week IS 'Week number (0 = playoffs/exhibition, 1-15 = regular season)';
COMMENT ON COLUMN matches.machines IS 'Array of machine keys available at venue for this match (from match JSON)';

-- Games table
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    match_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL CHECK (round_number BETWEEN 1 AND 4),
    game_number INTEGER NOT NULL DEFAULT 1,
    machine_key VARCHAR(50) NOT NULL,
    done BOOLEAN DEFAULT false,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    venue_key VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (match_key, round_number, game_number)
);

COMMENT ON TABLE games IS 'Individual game instances';
COMMENT ON COLUMN games.round_number IS 'Round 1,4 = 4-player; Round 2,3 = 2-player';

-- Scores table (heavily denormalized for query performance)
CREATE TABLE scores (
    score_id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_key VARCHAR(64) NOT NULL,
    player_position INTEGER NOT NULL CHECK (player_position BETWEEN 1 AND 4),
    score BIGINT NOT NULL CHECK (score >= 0),
    team_key VARCHAR(10) NOT NULL,
    is_home_team BOOLEAN NOT NULL,
    player_ipr INTEGER CHECK (player_ipr BETWEEN 1 AND 6),
    is_substitute BOOLEAN DEFAULT false,
    match_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_scores_game_player_position UNIQUE (game_id, player_key, player_position)
);

COMMENT ON TABLE scores IS 'Individual player scores with full context';
COMMENT ON COLUMN scores.player_position IS '1-4: position in game (reliability varies)';
COMMENT ON COLUMN scores.player_ipr IS 'IPR at time of match (snapshot)';
COMMENT ON COLUMN scores.is_substitute IS 'True if player was a substitute (not on official roster)';
COMMENT ON CONSTRAINT uq_scores_game_player_position ON scores IS 'Ensures a player can only have one score per position in a game';

-- ============================================================================
-- AGGREGATE/CACHE TABLES
-- ============================================================================

-- Score percentiles (pre-calculated)
CREATE TABLE score_percentiles (
    id SERIAL PRIMARY KEY,
    machine_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10),
    season INTEGER NOT NULL,
    percentile INTEGER NOT NULL CHECK (percentile BETWEEN 0 AND 100),
    score_threshold BIGINT NOT NULL,
    sample_size INTEGER NOT NULL,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (machine_key, venue_key, season, percentile)
);

COMMENT ON TABLE score_percentiles IS 'Pre-calculated percentile thresholds';
COMMENT ON COLUMN score_percentiles.venue_key IS '_ALL_ = all venues combined';

-- Player machine stats (aggregated)
CREATE TABLE player_machine_stats (
    player_key VARCHAR(64) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10) NOT NULL,
    season INTEGER NOT NULL,
    games_played INTEGER NOT NULL,
    total_score BIGINT,
    median_score BIGINT,
    avg_score BIGINT,
    best_score BIGINT,
    worst_score BIGINT,
    median_percentile DECIMAL(5,2),
    avg_percentile DECIMAL(5,2),
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_key, machine_key, venue_key, season)
);

COMMENT ON TABLE player_machine_stats IS 'Aggregated player performance by machine';
COMMENT ON COLUMN player_machine_stats.venue_key IS '_ALL_ = all venues combined';

-- Team machine picks (aggregated)
CREATE TABLE team_machine_picks (
    team_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    is_home BOOLEAN NOT NULL,
    round_type VARCHAR(10) NOT NULL CHECK (round_type IN ('singles', 'doubles')),
    times_picked INTEGER NOT NULL DEFAULT 0,
    total_opportunities INTEGER DEFAULT 0,
    wilson_lower DECIMAL(5,4) DEFAULT 0,
    wins INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    avg_score BIGINT,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_key, machine_key, season, is_home, round_type)
);

COMMENT ON TABLE team_machine_picks IS 'Aggregated team machine selection patterns';
COMMENT ON COLUMN team_machine_picks.total_opportunities IS 'Number of matches where team could pick this machine (machine was available at venue)';
COMMENT ON COLUMN team_machine_picks.wilson_lower IS 'Wilson score lower bound (95% CI) for pick rate - used for confidence-weighted sorting';

-- ============================================================================
-- MATCHPLAY.EVENTS INTEGRATION TABLES
-- ============================================================================

-- Matchplay player mappings
CREATE TABLE matchplay_player_mappings (
    id SERIAL PRIMARY KEY,
    mnp_player_key VARCHAR(64) NOT NULL UNIQUE,
    matchplay_user_id INTEGER NOT NULL UNIQUE,
    matchplay_name VARCHAR(255),
    ifpa_id INTEGER,
    match_method VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP
);

COMMENT ON TABLE matchplay_player_mappings IS 'Maps MNP players to Matchplay.events user profiles';
COMMENT ON COLUMN matchplay_player_mappings.mnp_player_key IS 'MNP player key (references players table)';
COMMENT ON COLUMN matchplay_player_mappings.matchplay_user_id IS 'Matchplay.events userId';
COMMENT ON COLUMN matchplay_player_mappings.matchplay_name IS 'Name as it appears on Matchplay';
COMMENT ON COLUMN matchplay_player_mappings.ifpa_id IS 'IFPA player ID if available';
COMMENT ON COLUMN matchplay_player_mappings.match_method IS 'How the match was made: auto (100% name match) or manual';
COMMENT ON COLUMN matchplay_player_mappings.last_synced IS 'When data was last fetched from Matchplay API';

-- Matchplay ratings
CREATE TABLE matchplay_ratings (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL,
    rating_value DECIMAL(8,2),
    rating_rd DECIMAL(6,2),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matchplay_ratings IS 'Cached Matchplay ratings for linked players';
COMMENT ON COLUMN matchplay_ratings.rating_value IS 'Matchplay rating value';
COMMENT ON COLUMN matchplay_ratings.rating_rd IS 'Rating deviation (lower = more certain)';

-- Matchplay player machine stats
CREATE TABLE matchplay_player_machine_stats (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL,
    machine_key VARCHAR(50),
    matchplay_arena_name VARCHAR(255) NOT NULL,
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_percentage DECIMAL(5,2),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(matchplay_user_id, matchplay_arena_name)
);

COMMENT ON TABLE matchplay_player_machine_stats IS 'Cached machine statistics from Matchplay for linked players';
COMMENT ON COLUMN matchplay_player_machine_stats.machine_key IS 'MNP machine key if mapped, NULL otherwise';
COMMENT ON COLUMN matchplay_player_machine_stats.matchplay_arena_name IS 'Machine/arena name as it appears in Matchplay';
COMMENT ON COLUMN matchplay_player_machine_stats.games_played IS 'Number of games played on this machine in Matchplay';
COMMENT ON COLUMN matchplay_player_machine_stats.wins IS 'Number of wins on this machine';
COMMENT ON COLUMN matchplay_player_machine_stats.win_percentage IS 'Calculated win percentage (0-100)';

-- Matchplay arena mappings (for machine name normalization)
CREATE TABLE matchplay_arena_mappings (
    matchplay_arena_name VARCHAR(255) PRIMARY KEY,
    machine_key VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matchplay_arena_mappings IS 'Maps Matchplay arena names to MNP machine keys';
COMMENT ON COLUMN matchplay_arena_mappings.matchplay_arena_name IS 'Arena/machine name as it appears in Matchplay';
COMMENT ON COLUMN matchplay_arena_mappings.machine_key IS 'Corresponding MNP machine key';

-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================

CREATE TABLE schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
    ('2.2.0', 'Consolidated schema with match machines and opportunity tracking');

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Players indexes
CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_ipr ON players(current_ipr);
CREATE INDEX idx_players_season ON players(last_seen_season);

-- Teams indexes
CREATE INDEX idx_teams_venue ON teams(home_venue_key, season);
CREATE INDEX idx_teams_season ON teams(season);

-- Team aliases indexes
CREATE INDEX idx_team_aliases_team_key ON team_aliases(team_key);

-- Venues indexes
CREATE INDEX idx_venues_active ON venues(active);
CREATE INDEX idx_venues_name ON venues(venue_name);

-- Machines indexes
CREATE INDEX idx_machines_name ON machines(machine_name);
CREATE INDEX idx_machines_manufacturer ON machines(manufacturer);

-- Machine aliases indexes
CREATE INDEX idx_aliases_machine ON machine_aliases(machine_key);

-- Venue machines indexes
CREATE INDEX idx_venue_machines_venue ON venue_machines(venue_key, season, active);
CREATE INDEX idx_venue_machines_machine ON venue_machines(machine_key, season);

-- Matches indexes
CREATE INDEX idx_matches_season_week ON matches(season, week);
CREATE INDEX idx_matches_venue ON matches(venue_key, season);
CREATE INDEX idx_matches_teams ON matches(home_team_key, away_team_key, season);
CREATE INDEX idx_matches_date ON matches(date);
CREATE INDEX idx_matches_state ON matches(state);
CREATE INDEX idx_matches_machines ON matches USING GIN (machines);

-- Games indexes
CREATE INDEX idx_games_match ON games(match_key);
CREATE INDEX idx_games_machine ON games(machine_key, season);
CREATE INDEX idx_games_machine_venue ON games(machine_key, venue_key, season);
CREATE INDEX idx_games_season_week ON games(season, week);

-- Scores indexes (critical for performance)
CREATE INDEX idx_scores_player_machine ON scores(player_key, machine_key, season);
CREATE INDEX idx_scores_player_venue ON scores(player_key, venue_key, season);
CREATE INDEX idx_scores_player_season ON scores(player_key, season);
CREATE INDEX idx_scores_machine_venue ON scores(machine_key, venue_key, season);
CREATE INDEX idx_scores_machine_score ON scores(machine_key, score);
CREATE INDEX idx_scores_machine_season ON scores(machine_key, season);
CREATE INDEX idx_scores_team ON scores(team_key, season);
CREATE INDEX idx_scores_team_machine ON scores(team_key, machine_key, season);
CREATE INDEX idx_scores_game ON scores(game_id);
CREATE INDEX idx_scores_season_week ON scores(season, week);
CREATE INDEX idx_scores_venue_season ON scores(venue_key, season);
CREATE INDEX idx_scores_round_type ON scores(round_number, season);
CREATE INDEX idx_scores_home_away ON scores(is_home_team, season);
CREATE INDEX idx_scores_match_round_machine ON scores(match_key, round_number, machine_key);
CREATE INDEX idx_scores_team_season ON scores(team_key, season);
CREATE INDEX idx_scores_venue ON scores(venue_key);
CREATE INDEX idx_scores_substitute ON scores(is_substitute);
CREATE INDEX idx_scores_team_season_venue ON scores(team_key, season, venue_key);
CREATE INDEX idx_scores_player_team ON scores(player_key, team_key);

-- Score percentiles indexes
CREATE INDEX idx_percentiles_lookup ON score_percentiles(machine_key, venue_key, season);
CREATE INDEX idx_percentiles_machine ON score_percentiles(machine_key, season);

-- Player machine stats indexes
CREATE INDEX idx_player_stats_player ON player_machine_stats(player_key, season);
CREATE INDEX idx_player_stats_best_machines ON player_machine_stats(player_key, venue_key, season, median_percentile DESC);
CREATE INDEX idx_player_stats_machine ON player_machine_stats(machine_key, season);

-- Team machine picks indexes
CREATE INDEX idx_team_picks_team ON team_machine_picks(team_key, season, is_home, round_type, times_picked DESC);
CREATE INDEX idx_team_picks_machine ON team_machine_picks(machine_key, season);
CREATE INDEX idx_team_machine_picks_wilson ON team_machine_picks(season, round_type, wilson_lower DESC);

-- Matchplay indexes
CREATE INDEX idx_mp_mappings_mnp ON matchplay_player_mappings(mnp_player_key);
CREATE INDEX idx_mp_mappings_mp_user ON matchplay_player_mappings(matchplay_user_id);
CREATE INDEX idx_mp_ratings_user ON matchplay_ratings(matchplay_user_id);
CREATE INDEX idx_mp_ratings_fetched ON matchplay_ratings(fetched_at DESC);
CREATE INDEX idx_mp_machine_stats_user ON matchplay_player_machine_stats(matchplay_user_id);
CREATE INDEX idx_mp_machine_stats_machine ON matchplay_player_machine_stats(machine_key);
CREATE INDEX idx_arena_mappings_machine ON matchplay_arena_mappings(machine_key);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Machine aliases constraints
ALTER TABLE machine_aliases
    ADD CONSTRAINT fk_machine_aliases_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- Venue machines constraints
ALTER TABLE venue_machines
    ADD CONSTRAINT fk_venue_machines_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE CASCADE;

ALTER TABLE venue_machines
    ADD CONSTRAINT fk_venue_machines_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- Teams constraints
ALTER TABLE teams
    ADD CONSTRAINT fk_teams_venue
    FOREIGN KEY (home_venue_key)
    REFERENCES venues(venue_key)
    ON DELETE SET NULL;

-- Matches constraints
ALTER TABLE matches
    ADD CONSTRAINT fk_matches_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE RESTRICT;

ALTER TABLE matches
    ADD CONSTRAINT fk_matches_home_team
    FOREIGN KEY (home_team_key, season)
    REFERENCES teams(team_key, season)
    ON DELETE RESTRICT;

ALTER TABLE matches
    ADD CONSTRAINT fk_matches_away_team
    FOREIGN KEY (away_team_key, season)
    REFERENCES teams(team_key, season)
    ON DELETE RESTRICT;

-- Games constraints
ALTER TABLE games
    ADD CONSTRAINT fk_games_match
    FOREIGN KEY (match_key)
    REFERENCES matches(match_key)
    ON DELETE CASCADE;

ALTER TABLE games
    ADD CONSTRAINT fk_games_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE RESTRICT;

ALTER TABLE games
    ADD CONSTRAINT fk_games_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE RESTRICT;

-- Scores constraints
ALTER TABLE scores
    ADD CONSTRAINT fk_scores_game
    FOREIGN KEY (game_id)
    REFERENCES games(game_id)
    ON DELETE CASCADE;

ALTER TABLE scores
    ADD CONSTRAINT fk_scores_player
    FOREIGN KEY (player_key)
    REFERENCES players(player_key)
    ON DELETE CASCADE;

ALTER TABLE scores
    ADD CONSTRAINT fk_scores_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE RESTRICT;

ALTER TABLE scores
    ADD CONSTRAINT fk_scores_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE RESTRICT;

ALTER TABLE scores
    ADD CONSTRAINT fk_scores_match
    FOREIGN KEY (match_key)
    REFERENCES matches(match_key)
    ON DELETE CASCADE;

-- Score percentiles constraints
ALTER TABLE score_percentiles
    ADD CONSTRAINT fk_percentiles_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- Player machine stats constraints
ALTER TABLE player_machine_stats
    ADD CONSTRAINT fk_player_stats_player
    FOREIGN KEY (player_key)
    REFERENCES players(player_key)
    ON DELETE CASCADE;

ALTER TABLE player_machine_stats
    ADD CONSTRAINT fk_player_stats_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- Team machine picks constraints
ALTER TABLE team_machine_picks
    ADD CONSTRAINT fk_team_picks_team
    FOREIGN KEY (team_key, season)
    REFERENCES teams(team_key, season)
    ON DELETE CASCADE;

ALTER TABLE team_machine_picks
    ADD CONSTRAINT fk_team_picks_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- Matchplay constraints
ALTER TABLE matchplay_player_mappings
    ADD CONSTRAINT fk_mnp_player
    FOREIGN KEY (mnp_player_key)
    REFERENCES players(player_key)
    ON DELETE CASCADE;

ALTER TABLE matchplay_ratings
    ADD CONSTRAINT fk_mp_rating_user
    FOREIGN KEY (matchplay_user_id)
    REFERENCES matchplay_player_mappings(matchplay_user_id)
    ON DELETE CASCADE;

ALTER TABLE matchplay_player_machine_stats
    ADD CONSTRAINT fk_mp_machine_stats_user
    FOREIGN KEY (matchplay_user_id)
    REFERENCES matchplay_player_mappings(matchplay_user_id)
    ON DELETE CASCADE;

ALTER TABLE matchplay_player_machine_stats
    ADD CONSTRAINT fk_mp_machine_stats_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE SET NULL;

ALTER TABLE matchplay_arena_mappings
    ADD CONSTRAINT fk_arena_mapping_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE SET NULL;

-- ============================================================================
-- CHECK CONSTRAINTS
-- ============================================================================

-- Note: Removed score limit constraint - source data has some very high scores (data entry errors)
-- that we need to load. Filtering should happen at query/display time if needed.

-- Ensure percentile is valid
ALTER TABLE score_percentiles
    ADD CONSTRAINT chk_percentile_range
    CHECK (percentile >= 0 AND percentile <= 100);

-- Ensure sample size is positive
ALTER TABLE score_percentiles
    ADD CONSTRAINT chk_sample_size_positive
    CHECK (sample_size > 0);

-- Ensure games played is positive
ALTER TABLE player_machine_stats
    ADD CONSTRAINT chk_games_played_positive
    CHECK (games_played > 0);

-- Ensure median percentile is valid
ALTER TABLE player_machine_stats
    ADD CONSTRAINT chk_median_percentile_range
    CHECK (median_percentile IS NULL OR (median_percentile >= 0 AND median_percentile <= 100));

-- Ensure times picked is non-negative
ALTER TABLE team_machine_picks
    ADD CONSTRAINT chk_times_picked_nonnegative
    CHECK (times_picked >= 0);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Known team aliases (e.g., Contras -> Trolls!)
INSERT INTO team_aliases (alias_key, team_key, alias_name, seasons_active)
VALUES ('CDC', 'TRL', 'Contras', '18,19,20,21')
ON CONFLICT (alias_key) DO NOTHING;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
    index_count INTEGER;
    fk_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints
    WHERE constraint_type = 'FOREIGN KEY'
    AND table_schema = 'public';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Schema created successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: %', table_count;
    RAISE NOTICE 'Indexes created: %', index_count;
    RAISE NOTICE 'Foreign keys: %', fk_count;
    RAISE NOTICE '========================================';
END $$;
