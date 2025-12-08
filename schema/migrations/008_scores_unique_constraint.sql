-- MNP Analyzer: Add unique constraint to scores table
-- Version: 1.0.0
-- Created: 2025-12-02
-- Description: Fix duplicate scores by adding unique constraint
--
-- Problem: The scores table had no unique constraint, so running load_season.py
-- multiple times would insert duplicate rows (ON CONFLICT DO NOTHING had no effect).

-- ============================================================================
-- STEP 1: Remove duplicate scores (keep the first inserted row by score_id)
-- ============================================================================

-- Count duplicates before deletion (for logging)
DO $$
DECLARE
    dup_count INTEGER;
BEGIN
    SELECT COUNT(*) - COUNT(DISTINCT (game_id, player_key, player_position))
    INTO dup_count
    FROM scores;

    RAISE NOTICE 'Found % duplicate score rows to remove', dup_count;
END $$;

-- Delete duplicates, keeping the row with the lowest score_id
DELETE FROM scores a
USING scores b
WHERE a.score_id > b.score_id
  AND a.game_id = b.game_id
  AND a.player_key = b.player_key
  AND a.player_position = b.player_position;

-- ============================================================================
-- STEP 2: Add unique constraint to prevent future duplicates
-- ============================================================================

ALTER TABLE scores
    ADD CONSTRAINT uq_scores_game_player_position
    UNIQUE (game_id, player_key, player_position);

COMMENT ON CONSTRAINT uq_scores_game_player_position ON scores IS
    'Ensures a player can only have one score per position in a game';

-- ============================================================================
-- STEP 3: Update schema version
-- ============================================================================

INSERT INTO schema_version (version, description) VALUES
    ('1.0.8', 'Add unique constraint to scores table to prevent duplicates');

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
DECLARE
    score_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO score_count FROM scores;

    RAISE NOTICE 'Migration complete!';
    RAISE NOTICE 'Unique constraint added to scores table';
    RAISE NOTICE 'Total scores after deduplication: %', score_count;
END $$;
