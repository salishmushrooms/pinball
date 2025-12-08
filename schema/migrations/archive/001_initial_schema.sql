-- MNP Analyzer Database Schema
-- Version: 1.0.0
-- Created: 2025-01-23
-- Description: Initial schema with core tables

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

-- Venues table
CREATE TABLE venues (
    venue_key VARCHAR(10) PRIMARY KEY,
    venue_name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(2),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE venues IS 'Venue information';
COMMENT ON COLUMN venues.venue_key IS '3-4 letter venue code (e.g., T4B, JUP)';

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

-- Matches table
CREATE TABLE matches (
    match_key VARCHAR(50) PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL CHECK (week BETWEEN 1 AND 15),
    date DATE,
    venue_key VARCHAR(10) NOT NULL,
    home_team_key VARCHAR(10) NOT NULL,
    away_team_key VARCHAR(10) NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    home_team_points INTEGER,
    away_team_points INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE matches IS 'Match metadata';
COMMENT ON COLUMN matches.match_key IS 'Format: mnp-{season}-{week}-{away}-{home}';
COMMENT ON COLUMN matches.state IS 'Match status: scheduled, playing, complete';

-- Games table
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    match_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL CHECK (round_number BETWEEN 1 AND 4),
    game_number INTEGER NOT NULL DEFAULT 1,
    machine_key VARCHAR(50) NOT NULL,
    done BOOLEAN DEFAULT false,
    -- Denormalized for query performance
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
    -- Denormalized fields for query performance
    match_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    round_number INTEGER NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE scores IS 'Individual player scores with full context';
COMMENT ON COLUMN scores.player_position IS '1-4: position in game (reliability varies)';
COMMENT ON COLUMN scores.player_ipr IS 'IPR at time of match (snapshot)';

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
COMMENT ON COLUMN score_percentiles.venue_key IS 'NULL = all venues combined';

-- Player machine stats (aggregated)
CREATE TABLE player_machine_stats (
    player_key VARCHAR(64) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    venue_key VARCHAR(10),
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
COMMENT ON COLUMN player_machine_stats.venue_key IS 'NULL = all venues combined';

-- Team machine picks (aggregated)
CREATE TABLE team_machine_picks (
    team_key VARCHAR(10) NOT NULL,
    machine_key VARCHAR(50) NOT NULL,
    season INTEGER NOT NULL,
    is_home BOOLEAN NOT NULL,
    round_type VARCHAR(10) NOT NULL CHECK (round_type IN ('singles', 'doubles')),
    times_picked INTEGER NOT NULL DEFAULT 0,
    wins INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    avg_score BIGINT,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_key, machine_key, season, is_home, round_type)
);

COMMENT ON TABLE team_machine_picks IS 'Aggregated team machine selection patterns';

-- ============================================================================
-- SCHEMA VERSION TRACKING
-- ============================================================================

CREATE TABLE schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
    ('1.0.0', 'Initial schema with core tables and aggregate tables');

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Schema created successfully!';
    RAISE NOTICE 'Tables created: 12 core + 3 aggregate + 1 version = 16 total';
END $$;
