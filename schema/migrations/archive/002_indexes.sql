-- MNP Analyzer Database Indexes
-- Version: 1.0.0
-- Created: 2025-01-23
-- Description: Strategic indexes for query performance

-- ============================================================================
-- PLAYERS TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_ipr ON players(current_ipr);
CREATE INDEX idx_players_season ON players(last_seen_season);

COMMENT ON INDEX idx_players_name IS 'For player search by name';
COMMENT ON INDEX idx_players_ipr IS 'For filtering by IPR range';

-- ============================================================================
-- TEAMS TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_teams_venue ON teams(home_venue_key, season);
CREATE INDEX idx_teams_season ON teams(season);

COMMENT ON INDEX idx_teams_venue IS 'For finding teams by home venue';

-- ============================================================================
-- VENUES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_venues_active ON venues(active);
CREATE INDEX idx_venues_name ON venues(venue_name);

-- ============================================================================
-- MACHINES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_machines_name ON machines(machine_name);
CREATE INDEX idx_machines_manufacturer ON machines(manufacturer);

-- ============================================================================
-- MACHINE ALIASES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_aliases_machine ON machine_aliases(machine_key);

COMMENT ON INDEX idx_aliases_machine IS 'For looking up all aliases of a machine';

-- ============================================================================
-- VENUE MACHINES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_venue_machines_venue ON venue_machines(venue_key, season, active);
CREATE INDEX idx_venue_machines_machine ON venue_machines(machine_key, season);

COMMENT ON INDEX idx_venue_machines_venue IS 'For finding machines at a venue';
COMMENT ON INDEX idx_venue_machines_machine IS 'For finding which venues have a machine';

-- ============================================================================
-- MATCHES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_matches_season_week ON matches(season, week);
CREATE INDEX idx_matches_venue ON matches(venue_key, season);
CREATE INDEX idx_matches_teams ON matches(home_team_key, away_team_key, season);
CREATE INDEX idx_matches_date ON matches(date);
CREATE INDEX idx_matches_state ON matches(state);

COMMENT ON INDEX idx_matches_season_week IS 'For browsing matches by season/week';
COMMENT ON INDEX idx_matches_venue IS 'For all matches at a venue';
COMMENT ON INDEX idx_matches_teams IS 'For team matchup history';

-- ============================================================================
-- GAMES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_games_match ON games(match_key);
CREATE INDEX idx_games_machine ON games(machine_key, season);
CREATE INDEX idx_games_machine_venue ON games(machine_key, venue_key, season);
CREATE INDEX idx_games_season_week ON games(season, week);

COMMENT ON INDEX idx_games_machine IS 'For all games on a specific machine';
COMMENT ON INDEX idx_games_machine_venue IS 'For machine stats at specific venue';

-- ============================================================================
-- SCORES TABLE INDEXES (CRITICAL FOR PERFORMANCE)
-- ============================================================================

-- Player queries
CREATE INDEX idx_scores_player_machine ON scores(player_key, machine_key, season);
CREATE INDEX idx_scores_player_venue ON scores(player_key, venue_key, season);
CREATE INDEX idx_scores_player_season ON scores(player_key, season);

-- Machine queries
CREATE INDEX idx_scores_machine_venue ON scores(machine_key, venue_key, season);
CREATE INDEX idx_scores_machine_score ON scores(machine_key, score);
CREATE INDEX idx_scores_machine_season ON scores(machine_key, season);

-- Team queries
CREATE INDEX idx_scores_team ON scores(team_key, season);
CREATE INDEX idx_scores_team_machine ON scores(team_key, machine_key, season);

-- General queries
CREATE INDEX idx_scores_game ON scores(game_id);
CREATE INDEX idx_scores_season_week ON scores(season, week);
CREATE INDEX idx_scores_venue_season ON scores(venue_key, season);

-- Round type queries (for singles vs doubles)
CREATE INDEX idx_scores_round_type ON scores(round_number, season);

-- Home/away split queries
CREATE INDEX idx_scores_home_away ON scores(is_home_team, season);

COMMENT ON INDEX idx_scores_player_machine IS 'CRITICAL: Player performance on specific machine';
COMMENT ON INDEX idx_scores_machine_venue IS 'CRITICAL: Machine performance at venue (for percentiles)';
COMMENT ON INDEX idx_scores_machine_score IS 'For percentile calculations and ranking';

-- ============================================================================
-- SCORE PERCENTILES TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_percentiles_lookup ON score_percentiles(machine_key, venue_key, season);
CREATE INDEX idx_percentiles_machine ON score_percentiles(machine_key, season);

COMMENT ON INDEX idx_percentiles_lookup IS 'CRITICAL: Fast percentile lookups';

-- ============================================================================
-- PLAYER MACHINE STATS TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_player_stats_player ON player_machine_stats(player_key, season);
CREATE INDEX idx_player_stats_best_machines ON player_machine_stats(
    player_key,
    venue_key,
    season,
    median_percentile DESC
);
CREATE INDEX idx_player_stats_machine ON player_machine_stats(machine_key, season);

COMMENT ON INDEX idx_player_stats_best_machines IS 'CRITICAL: Best machines for player at venue';

-- ============================================================================
-- TEAM MACHINE PICKS TABLE INDEXES
-- ============================================================================

CREATE INDEX idx_team_picks_team ON team_machine_picks(
    team_key,
    season,
    is_home,
    round_type,
    times_picked DESC
);
CREATE INDEX idx_team_picks_machine ON team_machine_picks(machine_key, season);

COMMENT ON INDEX idx_team_picks_team IS 'CRITICAL: Most picked machines by team';

-- ============================================================================
-- ANALYZE TABLES
-- ============================================================================

-- Update table statistics for query planner
ANALYZE players;
ANALYZE teams;
ANALYZE venues;
ANALYZE machines;
ANALYZE machine_aliases;
ANALYZE venue_machines;
ANALYZE matches;
ANALYZE games;
ANALYZE scores;
ANALYZE score_percentiles;
ANALYZE player_machine_stats;
ANALYZE team_machine_picks;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE 'Indexes created successfully!';
    RAISE NOTICE 'Total indexes: %', index_count;
    RAISE NOTICE 'Tables analyzed for query optimization';
END $$;
