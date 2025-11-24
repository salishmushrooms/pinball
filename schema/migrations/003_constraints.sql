-- MNP Analyzer Foreign Key Constraints
-- Version: 1.0.0
-- Created: 2025-01-23
-- Description: Add foreign key relationships for referential integrity

-- NOTE: Foreign keys are added AFTER indexes for better performance

-- ============================================================================
-- MACHINE ALIASES CONSTRAINTS
-- ============================================================================

ALTER TABLE machine_aliases
    ADD CONSTRAINT fk_machine_aliases_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

-- ============================================================================
-- VENUE MACHINES CONSTRAINTS
-- ============================================================================

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

-- ============================================================================
-- TEAMS CONSTRAINTS
-- ============================================================================

ALTER TABLE teams
    ADD CONSTRAINT fk_teams_venue
    FOREIGN KEY (home_venue_key)
    REFERENCES venues(venue_key)
    ON DELETE SET NULL;

-- ============================================================================
-- MATCHES CONSTRAINTS
-- ============================================================================

ALTER TABLE matches
    ADD CONSTRAINT fk_matches_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE RESTRICT;

-- Note: Team foreign keys with composite key
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

-- ============================================================================
-- GAMES CONSTRAINTS
-- ============================================================================

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

-- ============================================================================
-- SCORES CONSTRAINTS
-- ============================================================================

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

-- ============================================================================
-- SCORE PERCENTILES CONSTRAINTS
-- ============================================================================

ALTER TABLE score_percentiles
    ADD CONSTRAINT fk_percentiles_machine
    FOREIGN KEY (machine_key)
    REFERENCES machines(machine_key)
    ON DELETE CASCADE;

ALTER TABLE score_percentiles
    ADD CONSTRAINT fk_percentiles_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE CASCADE;

-- ============================================================================
-- PLAYER MACHINE STATS CONSTRAINTS
-- ============================================================================

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

ALTER TABLE player_machine_stats
    ADD CONSTRAINT fk_player_stats_venue
    FOREIGN KEY (venue_key)
    REFERENCES venues(venue_key)
    ON DELETE CASCADE;

-- ============================================================================
-- TEAM MACHINE PICKS CONSTRAINTS
-- ============================================================================

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

-- ============================================================================
-- ADDITIONAL CHECK CONSTRAINTS
-- ============================================================================

-- Ensure scores don't exceed reasonable limits
ALTER TABLE scores
    ADD CONSTRAINT chk_scores_reasonable
    CHECK (score <= 10000000000);

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
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
DECLARE
    fk_count INTEGER;
    check_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO fk_count
    FROM information_schema.table_constraints
    WHERE constraint_type = 'FOREIGN KEY'
    AND table_schema = 'public';

    SELECT COUNT(*) INTO check_count
    FROM information_schema.table_constraints
    WHERE constraint_type = 'CHECK'
    AND table_schema = 'public';

    RAISE NOTICE 'Foreign key constraints added successfully!';
    RAISE NOTICE 'Total foreign keys: %', fk_count;
    RAISE NOTICE 'Total check constraints: %', check_count;
    RAISE NOTICE 'Referential integrity enforced';
END $$;
