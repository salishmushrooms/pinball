-- Migration: Add Pinball Map integration
-- Version: 2.3.1
-- Created: 2026-02-03
-- Description: Adds pinballmap_location_id to venues for Pinball Map API integration

-- Add pinballmap_location_id column to venues table
ALTER TABLE venues ADD COLUMN IF NOT EXISTS pinballmap_location_id INTEGER;

COMMENT ON COLUMN venues.pinballmap_location_id IS 'Pinball Map location ID for fetching current machine lineup';

-- Create index for lookups
CREATE INDEX IF NOT EXISTS idx_venues_pinballmap ON venues(pinballmap_location_id) WHERE pinballmap_location_id IS NOT NULL;

-- Populate known venue mappings (Seattle area MNP venues)
-- These IDs were found via Pinball Map API autocomplete search
UPDATE venues SET pinballmap_location_id = 1410 WHERE venue_key = 'AAB';  -- Add-a-Ball
UPDATE venues SET pinballmap_location_id = 4295 WHERE venue_key = '8BT';  -- 8-Bit Arcade Bar (Renton)
UPDATE venues SET pinballmap_location_id = 8947 WHERE venue_key = 'JUP';  -- Jupiter Gameroom
UPDATE venues SET pinballmap_location_id = 22987 WHERE venue_key = 'KRA'; -- The Kraken Bar & Lounge
UPDATE venues SET pinballmap_location_id = 1126 WHERE venue_key = 'SHR';  -- Shorty's

-- Update schema version
INSERT INTO schema_version (version, description)
VALUES ('2.3.1', 'Add Pinball Map integration to venues')
ON CONFLICT (version) DO NOTHING;
