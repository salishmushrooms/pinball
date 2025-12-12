-- Populate venue metadata from venues.json data
-- Run this after 002_venues_neighborhood.sql
-- Data sourced from mnp-data-archive/venues.json

UPDATE venues SET address = '5811 Airport Way S, Seattle, WA 98108', neighborhood = 'Georgetown' WHERE venue_key = 'STN';
UPDATE venues SET address = '5453 Leary Ave NW, Seattle', neighborhood = 'Ballard' WHERE venue_key = 'FTB';
UPDATE venues SET address = '6301 24th Ave NW, Seattle', neighborhood = 'Ballard' WHERE venue_key = 'OLF';
UPDATE venues SET address = '2222 2nd Ave, Seattle', neighborhood = 'Belltown' WHERE venue_key = 'SHR';
UPDATE venues SET address = '1351 E Olive Way, Seattle', neighborhood = 'Capital Hill' WHERE venue_key = 'JJS';
UPDATE venues SET address = '1118 East Pike Street, Seattle', neighborhood = 'Capital Hill' WHERE venue_key = 'NAR';
UPDATE venues SET address = '315 N 36th St #2b, Seattle', neighborhood = 'Fremont' WHERE venue_key = 'AAB';
UPDATE venues SET address = '2121 N 45th St, Seattle', neighborhood = 'Wallingford' WHERE venue_key = 'BUL';
UPDATE venues SET address = '105 W Mercer St, Seattle', neighborhood = 'Queen Anne' WHERE venue_key = 'OZS';
UPDATE venues SET address = '6012 12th Ave S, Seattle', neighborhood = 'Georgetown' WHERE venue_key = 'FFD';
UPDATE venues SET address = '916 S. 3rd st, Renton', neighborhood = NULL WHERE venue_key = '8BT';
UPDATE venues SET address = '10325 E Marginal Way S, Tukwila', neighborhood = NULL WHERE venue_key = 'LLQ';
UPDATE venues SET address = '23303 Highway 99, Suite A, Edmonds', neighborhood = NULL WHERE venue_key = 'ANC';
UPDATE venues SET address = '4358 Leary Way NW, Seattle, WA 98107', neighborhood = 'Frelard' WHERE venue_key = 'BJM';
UPDATE venues SET address = '6722 Greenwood Ave N, Seattle, WA 98103', neighborhood = 'Phinney Ridge' WHERE venue_key = 'GOA';

DO $$
BEGIN
    RAISE NOTICE 'Venue metadata populated for 15 venues';
END $$;
