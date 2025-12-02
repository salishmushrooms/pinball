# Matchplay.events Integration Plan

## Overview

This document outlines the integration of Matchplay.events data into the MNP application. The primary goals are:

1. **Player Details Page**: Display Matchplay rating, most played machines, and win % per machine
2. **Team Pages**: Include Matchplay rating in roster details
3. **Matchup Page**: Show Matchplay machine stats for each team filtered to venue-available machines
4. **Investigate**: Whether MNP match data is uploaded to Matchplay (could provide unified data source)

---

## Key Decisions (Resolved)

| Question | Decision |
|----------|----------|
| API Token | ✅ Available |
| Match Verification | Require manual confirmation unless 100% name match |
| Rating Display | Display Matchplay rating directly (IPR is derived from it) |
| Tournament Data | Yes, pull tournament participation for machine stats |
| Display Locations | Player details, team roster, matchup roster |

---

## API Understanding

### Matchplay.events API

**Base URL**: `https://app.matchplay.events`

**Authentication**: Bearer token (obtained from account settings → "API tokens")

**Rate Limits**: Indicated via response headers (`x-ratelimit-limit`, `x-ratelimit-remaining`)

### Key Endpoints for Integration

| Endpoint | Purpose | Data Needed |
|----------|---------|-------------|
| `GET /api/search?query={name}&type=users` | Find players by name | Player matching |
| `GET /api/ratings/{type}/{id}/summary` | Get rating summary | Matchplay rating value |
| `GET /api/tournaments` | List tournaments | Find MNP tournaments if they exist |
| `GET /api/tournaments/{id}/games` | Tournament game results | Win/loss data per machine |
| `GET /api/tournaments/{id}/single-player-games` | Individual scores | Machine play counts, scores |
| `GET /api/games?player={id}` | All games for a player | Machine statistics across all events |

### Player Identification

- **userId**: Internal Matchplay ID (integer)
- **ifpaId**: IFPA integration (integer, optional)
- **name**: Display name (string)

**Matching Strategy**:
- 100% name match → auto-link
- <100% match → require manual confirmation

---

## Data Requirements

### What We Need to Display

#### Player Details Page - Matchplay Section
```
┌─────────────────────────────────────────────────────────┐
│ Matchplay.events                                        │
├─────────────────────────────────────────────────────────┤
│ Rating: 1547.3                                          │
│ Profile: [Link to Matchplay profile]                    │
├─────────────────────────────────────────────────────────┤
│ Most Played Machines (from Matchplay)                   │
│ ┌─────────────────┬───────────┬─────────┐              │
│ │ Machine         │ Games     │ Win %   │              │
│ ├─────────────────┼───────────┼─────────┤              │
│ │ Medieval Madness│ 47        │ 62%     │              │
│ │ Attack From Mars│ 38        │ 55%     │              │
│ │ Twilight Zone   │ 31        │ 48%     │              │
│ │ ...             │           │         │              │
│ └─────────────────┴───────────┴─────────┘              │
└─────────────────────────────────────────────────────────┘
```

#### Team Page - Roster with Matchplay Rating
```
┌─────────────────────────────────────────────────────────┐
│ Team Roster                                             │
├─────────────────┬─────┬──────────────┬─────────────────┤
│ Player          │ IPR │ MP Rating    │ Games Played    │
├─────────────────┼─────┼──────────────┼─────────────────┤
│ John Smith      │ 4   │ 1547         │ 156             │
│ Jane Doe        │ 5   │ 1623         │ 203             │
│ ...             │     │              │                 │
└─────────────────┴─────┴──────────────┴─────────────────┘
```

#### Matchup Page - Team Matchplay Stats (per team tab)
```
┌─────────────────────────────────────────────────────────┐
│ Matchplay Stats at [Venue] Machines                     │
├─────────────────────────────────────────────────────────┤
│ Team aggregate stats on machines available at venue     │
│ ┌─────────────────┬───────────┬─────────┬────────────┐ │
│ │ Machine         │ Team Exp  │ Win %   │ Top Player │ │
│ ├─────────────────┼───────────┼─────────┼────────────┤ │
│ │ Medieval Madness│ 89 games  │ 58%     │ J. Smith   │ │
│ │ Attack From Mars│ 67 games  │ 52%     │ J. Doe     │ │
│ │ (venue machines)│           │         │            │ │
│ └─────────────────┴───────────┴─────────┴────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Investigation: MNP Data in Matchplay

**Question**: Is Monday Night Pinball match data uploaded to Matchplay.events?

**How to check**:
1. Search for tournaments with "Monday Night Pinball" or "MNP" in name
2. Check if MNP venue names appear as tournament locations
3. Compare game counts for known MNP players

If MNP data IS in Matchplay:
- Machine stats would include MNP performance
- Could use Matchplay as unified data source for external events

If MNP data is NOT in Matchplay:
- Matchplay stats represent non-MNP tournament play only
- Still valuable for understanding player experience on machines

---

## Database Schema

### Core Tables

```sql
-- 007_matchplay_integration.sql

-- Player mapping table
CREATE TABLE matchplay_player_mappings (
    id SERIAL PRIMARY KEY,
    mnp_player_key VARCHAR(64) NOT NULL REFERENCES players(player_key),
    matchplay_user_id INTEGER NOT NULL UNIQUE,
    matchplay_name VARCHAR(255),
    ifpa_id INTEGER,
    match_method VARCHAR(20) DEFAULT 'manual',  -- 'auto' (100% match), 'manual'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_synced TIMESTAMP,
    UNIQUE(mnp_player_key)
);

CREATE INDEX idx_mp_mappings_mnp ON matchplay_player_mappings(mnp_player_key);
CREATE INDEX idx_mp_mappings_mp ON matchplay_player_mappings(matchplay_user_id);

-- Cached Matchplay ratings
CREATE TABLE matchplay_ratings (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL REFERENCES matchplay_player_mappings(matchplay_user_id),
    rating_value DECIMAL(8,2),
    rating_rd DECIMAL(6,2),  -- Rating deviation
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mp_ratings_user ON matchplay_ratings(matchplay_user_id);

-- Cached machine statistics from Matchplay
CREATE TABLE matchplay_player_machine_stats (
    id SERIAL PRIMARY KEY,
    matchplay_user_id INTEGER NOT NULL REFERENCES matchplay_player_mappings(matchplay_user_id),
    machine_key VARCHAR(50),  -- Mapped to our machine_key if possible
    matchplay_arena_name VARCHAR(255),  -- Original name from Matchplay
    games_played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    win_percentage DECIMAL(5,2),
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(matchplay_user_id, matchplay_arena_name)
);

CREATE INDEX idx_mp_machine_stats_user ON matchplay_player_machine_stats(matchplay_user_id);
CREATE INDEX idx_mp_machine_stats_machine ON matchplay_player_machine_stats(machine_key);
```

### Machine Name Mapping Challenge

Matchplay uses "arena" names which may differ from our `machine_key`:
- Matchplay: "Medieval Madness (Williams, 1997)"
- MNP: "MM"

**Solution**: Create a mapping table or use fuzzy matching against `machine_variations.json`

```sql
-- Optional: explicit arena-to-machine mapping
CREATE TABLE matchplay_arena_mappings (
    matchplay_arena_name VARCHAR(255) PRIMARY KEY,
    machine_key VARCHAR(50) REFERENCES machines(machine_key),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Implementation Phases

### Phase 1: Foundation & Player Linking

#### 1.1 API Client Service

**New File**: `api/services/matchplay_client.py`

```python
"""
Matchplay.events API client.
"""
import httpx
import os
from typing import Optional, List, Dict, Any

class MatchplayClient:
    def __init__(self):
        self.base_url = "https://app.matchplay.events"
        self.token = os.getenv("MATCHPLAY_API_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search for users by name."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/search",
                params={"query": query, "type": "users"},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_rating_summary(self, user_id: int) -> Dict[str, Any]:
        """Get player rating summary."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/ratings/main/{user_id}/summary",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("data", {})

    async def get_player_games(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all games for a player (for machine statistics)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/games",
                params={"player": user_id},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def search_tournaments(self, query: str) -> List[Dict[str, Any]]:
        """Search for tournaments by name."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/search",
                params={"query": query, "type": "tournaments"},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json().get("data", [])
```

#### 1.2 Player Matching Logic

```python
# api/services/player_matcher.py

class PlayerMatcher:
    def __init__(self, client: MatchplayClient):
        self.client = client

    async def find_matches(self, mnp_name: str) -> List[Dict]:
        """
        Search Matchplay for players matching the MNP name.
        Returns list of potential matches with confidence scores.
        """
        results = await self.client.search_users(mnp_name)

        matches = []
        for user in results:
            mp_name = user.get("name", "")
            # Exact match = auto-link eligible
            is_exact = mp_name.lower().strip() == mnp_name.lower().strip()
            matches.append({
                "user": user,
                "confidence": 1.0 if is_exact else self._calculate_similarity(mnp_name, mp_name),
                "auto_link_eligible": is_exact
            })

        return sorted(matches, key=lambda x: x["confidence"], reverse=True)

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
```

#### 1.3 API Endpoints

**New File**: `api/routers/matchplay.py`

```python
router = APIRouter(prefix="/matchplay", tags=["matchplay"])

@router.get("/player/{player_key}/lookup")
async def lookup_player(player_key: str, db: Session = Depends(get_db)):
    """
    Look up MNP player on Matchplay. Returns potential matches.
    Only 100% name matches are auto-link eligible.
    """
    # Check if already linked
    existing = db.query(MatchplayMapping).filter_by(mnp_player_key=player_key).first()
    if existing:
        return {"status": "already_linked", "mapping": existing}

    # Get MNP player
    player = db.query(Player).filter_by(player_key=player_key).first()
    if not player:
        raise HTTPException(404, "Player not found")

    # Search Matchplay
    matches = await matcher.find_matches(player.name)

    return {
        "mnp_player": {"key": player_key, "name": player.name},
        "matches": matches,
        "status": "found" if matches else "not_found"
    }

@router.post("/player/{player_key}/link")
async def link_player(
    player_key: str,
    matchplay_user_id: int,
    db: Session = Depends(get_db)
):
    """Create link between MNP player and Matchplay user."""
    # Verify player exists
    player = db.query(Player).filter_by(player_key=player_key).first()
    if not player:
        raise HTTPException(404, "Player not found")

    # Get Matchplay user info
    client = MatchplayClient()
    # Fetch user details to store name

    # Create mapping
    mapping = MatchplayMapping(
        mnp_player_key=player_key,
        matchplay_user_id=matchplay_user_id,
        matchplay_name=matchplay_name,
        match_method="manual"
    )
    db.add(mapping)
    db.commit()

    return {"status": "linked", "mapping": mapping}

@router.get("/player/{player_key}/stats")
async def get_player_matchplay_stats(player_key: str, db: Session = Depends(get_db)):
    """
    Get Matchplay stats for a linked player.
    Returns rating and machine statistics.
    """
    mapping = db.query(MatchplayMapping).filter_by(mnp_player_key=player_key).first()
    if not mapping:
        raise HTTPException(404, "Player not linked to Matchplay")

    client = MatchplayClient()

    # Get rating
    rating = await client.get_rating_summary(mapping.matchplay_user_id)

    # Get machine stats (from cache or fetch)
    machine_stats = await get_or_fetch_machine_stats(mapping.matchplay_user_id, db)

    return {
        "rating": rating,
        "machine_stats": machine_stats,
        "matchplay_user_id": mapping.matchplay_user_id,
        "matchplay_name": mapping.matchplay_name
    }

@router.get("/team/{team_key}/matchplay-stats")
async def get_team_matchplay_stats(
    team_key: str,
    venue_key: Optional[str] = None,
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get aggregated Matchplay stats for a team's roster.
    Optionally filter machine stats to those available at a venue.
    """
    # Get team roster
    players = get_team_players(team_key, season, db)

    # Get Matchplay stats for each linked player
    team_stats = []
    for player in players:
        mapping = db.query(MatchplayMapping).filter_by(
            mnp_player_key=player.player_key
        ).first()

        if mapping:
            stats = await get_player_matchplay_stats(player.player_key, db)
            team_stats.append({
                "player": player,
                "matchplay": stats
            })

    # If venue specified, filter to venue machines
    if venue_key:
        venue_machines = get_venue_machines(venue_key, db)
        # Filter machine_stats to only include venue machines

    return team_stats
```

---

### Phase 2: Frontend Integration

#### 2.1 TypeScript Types

**Add to**: `frontend/lib/types.ts`

```typescript
// Matchplay integration types
export interface MatchplayLookupResult {
  mnp_player: { key: string; name: string };
  matches: MatchplayMatch[];
  status: 'found' | 'not_found' | 'already_linked';
  mapping?: MatchplayPlayerMapping;
}

export interface MatchplayMatch {
  user: MatchplayUser;
  confidence: number;
  auto_link_eligible: boolean;
}

export interface MatchplayUser {
  userId: number;
  name: string;
  ifpaId?: number;
}

export interface MatchplayPlayerMapping {
  mnp_player_key: string;
  matchplay_user_id: number;
  matchplay_name: string;
  match_method: 'auto' | 'manual';
  last_synced?: string;
}

export interface MatchplayRating {
  rating_value: number;
  rating_rd?: number;
}

export interface MatchplayMachineStat {
  machine_key?: string;
  matchplay_arena_name: string;
  games_played: number;
  wins: number;
  win_percentage: number;
}

export interface MatchplayPlayerStats {
  rating: MatchplayRating;
  machine_stats: MatchplayMachineStat[];
  matchplay_user_id: number;
  matchplay_name: string;
}

// Extended player types with Matchplay data
export interface PlayerWithMatchplay extends Player {
  matchplay?: MatchplayPlayerStats;
}

export interface TeamPlayerWithMatchplay extends TeamPlayer {
  matchplay_rating?: number;
}
```

#### 2.2 API Client Extensions

**Add to**: `frontend/lib/api.ts`

```typescript
// Matchplay endpoints
export async function lookupPlayerMatchplay(playerKey: string): Promise<MatchplayLookupResult> {
  const response = await fetch(`${API_BASE}/matchplay/player/${playerKey}/lookup`);
  if (!response.ok) throw new Error('Matchplay lookup failed');
  return response.json();
}

export async function linkPlayerToMatchplay(
  playerKey: string,
  matchplayUserId: number
): Promise<{ status: string; mapping: MatchplayPlayerMapping }> {
  const response = await fetch(`${API_BASE}/matchplay/player/${playerKey}/link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ matchplay_user_id: matchplayUserId })
  });
  if (!response.ok) throw new Error('Failed to link player');
  return response.json();
}

export async function getPlayerMatchplayStats(playerKey: string): Promise<MatchplayPlayerStats> {
  const response = await fetch(`${API_BASE}/matchplay/player/${playerKey}/stats`);
  if (!response.ok) throw new Error('Failed to fetch Matchplay stats');
  return response.json();
}

export async function getTeamMatchplayStats(
  teamKey: string,
  venueKey?: string,
  season?: number
): Promise<TeamPlayerWithMatchplay[]> {
  const params = new URLSearchParams();
  if (venueKey) params.append('venue_key', venueKey);
  if (season) params.append('season', season.toString());

  const response = await fetch(`${API_BASE}/matchplay/team/${teamKey}/matchplay-stats?${params}`);
  if (!response.ok) throw new Error('Failed to fetch team Matchplay stats');
  return response.json();
}
```

#### 2.3 Player Details Page Enhancement

**Update**: `frontend/app/players/[player_key]/page.tsx`

Add new section:

```tsx
// New component: MatchplaySection
function MatchplaySection({ playerKey }: { playerKey: string }) {
  const [matchplayData, setMatchplayData] = useState<MatchplayPlayerStats | null>(null);
  const [lookupResult, setLookupResult] = useState<MatchplayLookupResult | null>(null);
  const [isLinking, setIsLinking] = useState(false);

  useEffect(() => {
    // Try to fetch existing Matchplay data
    getPlayerMatchplayStats(playerKey)
      .then(setMatchplayData)
      .catch(() => {
        // Not linked yet, show lookup option
      });
  }, [playerKey]);

  const handleLookup = async () => {
    const result = await lookupPlayerMatchplay(playerKey);
    setLookupResult(result);
  };

  const handleLink = async (matchplayUserId: number) => {
    await linkPlayerToMatchplay(playerKey, matchplayUserId);
    // Refresh data
    const stats = await getPlayerMatchplayStats(playerKey);
    setMatchplayData(stats);
    setLookupResult(null);
  };

  if (matchplayData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Matchplay.events</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <span className="text-muted-foreground">Rating:</span>{' '}
            <span className="font-semibold">{matchplayData.rating.rating_value.toFixed(1)}</span>
            <a
              href={`https://app.matchplay.events/users/${matchplayData.matchplay_user_id}`}
              target="_blank"
              className="ml-4 text-blue-500 hover:underline"
            >
              View Profile →
            </a>
          </div>

          <h4 className="font-medium mb-2">Most Played Machines</h4>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Machine</TableHead>
                <TableHead>Games</TableHead>
                <TableHead>Win %</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {matchplayData.machine_stats
                .sort((a, b) => b.games_played - a.games_played)
                .slice(0, 10)
                .map(stat => (
                  <TableRow key={stat.matchplay_arena_name}>
                    <TableCell>{stat.matchplay_arena_name}</TableCell>
                    <TableCell>{stat.games_played}</TableCell>
                    <TableCell>{stat.win_percentage.toFixed(0)}%</TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    );
  }

  // Show lookup/link UI if not connected
  return (
    <Card>
      <CardHeader>
        <CardTitle>Matchplay.events</CardTitle>
      </CardHeader>
      <CardContent>
        {!lookupResult ? (
          <Button onClick={handleLookup}>Find on Matchplay</Button>
        ) : lookupResult.matches.length > 0 ? (
          <div>
            <p className="mb-2">Select the correct Matchplay profile:</p>
            {lookupResult.matches.map(match => (
              <div key={match.user.userId} className="flex items-center gap-4 py-2">
                <span>{match.user.name}</span>
                <span className="text-muted-foreground">
                  ({(match.confidence * 100).toFixed(0)}% match)
                </span>
                <Button
                  size="sm"
                  onClick={() => handleLink(match.user.userId)}
                >
                  {match.auto_link_eligible ? 'Link (Exact Match)' : 'Link'}
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <p>No Matchplay profile found</p>
        )}
      </CardContent>
    </Card>
  );
}
```

#### 2.4 Team Page - Roster Enhancement

Add Matchplay rating column to roster table.

#### 2.5 Matchup Page - Team Matchplay Stats

Add new tab/section under each team showing:
- Team's Matchplay machine stats filtered to venue machines
- Aggregated win % per machine
- Player with most experience on each machine

---

### Phase 3: Investigation & Data Sync

#### 3.1 Check for MNP in Matchplay

Create a script/endpoint to search for MNP tournaments:

```python
async def investigate_mnp_in_matchplay():
    """Check if MNP data exists in Matchplay."""
    client = MatchplayClient()

    # Search for MNP tournaments
    searches = [
        "Monday Night Pinball",
        "MNP",
        "MNP Seattle",
    ]

    results = {}
    for query in searches:
        tournaments = await client.search_tournaments(query)
        results[query] = tournaments

    return results
```

#### 3.2 Batch Player Sync

ETL script to link all MNP players:

```python
# etl/sync_matchplay_players.py

async def sync_all_players(auto_link_only: bool = True):
    """
    Attempt to link all MNP players to Matchplay.

    Args:
        auto_link_only: If True, only auto-link 100% name matches
    """
    unlinked = get_unlinked_players()

    results = {
        "auto_linked": [],
        "needs_review": [],
        "not_found": []
    }

    for player in unlinked:
        matches = await matcher.find_matches(player.name)

        if not matches:
            results["not_found"].append(player)
        elif matches[0]["auto_link_eligible"]:
            # 100% match - auto link
            create_mapping(player.player_key, matches[0]["user"]["userId"], "auto")
            results["auto_linked"].append(player)
        else:
            # Needs manual review
            results["needs_review"].append({
                "player": player,
                "matches": matches
            })

    return results
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Pages                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐ │
│  │ Player Details │  │ Team Page      │  │ Matchup Page           │ │
│  │ - MP Rating    │  │ - Roster + MP  │  │ - Team MP stats        │ │
│  │ - Machine stats│  │   ratings      │  │ - Venue machine filter │ │
│  │ - Link/lookup  │  │                │  │                        │ │
│  └───────┬────────┘  └───────┬────────┘  └───────────┬────────────┘ │
└──────────┼───────────────────┼───────────────────────┼──────────────┘
           │                   │                       │
           └───────────────────┼───────────────────────┘
                               │ API Calls
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                             │
│  /matchplay/player/{key}/lookup   → Search & match                  │
│  /matchplay/player/{key}/link     → Save mapping                    │
│  /matchplay/player/{key}/stats    → Rating + machine stats          │
│  /matchplay/team/{key}/stats      → Aggregated team stats           │
└──────────────┬─────────────────────────────────┬────────────────────┘
               │                                 │
               ▼                                 ▼
┌──────────────────────────┐       ┌──────────────────────────────────┐
│    MNP Database          │       │    Matchplay.events API          │
│  - Player mappings       │       │  - User search                   │
│  - Cached ratings        │       │  - Rating summaries              │
│  - Machine stats cache   │       │  - Game history (for stats)      │
│  - Arena→Machine mapping │       │  - Tournament search             │
└──────────────────────────┘       └──────────────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Add `MATCHPLAY_API_TOKEN` to environment
- [ ] Create database migration `007_matchplay_integration.sql`
- [ ] Implement `MatchplayClient` service
- [ ] Implement `PlayerMatcher` service
- [ ] Create `/matchplay/player/{key}/lookup` endpoint
- [ ] Create `/matchplay/player/{key}/link` endpoint
- [ ] Test with known players
- [ ] **Investigate**: Search for MNP tournaments in Matchplay

### Phase 2: Stats & Display
- [ ] Create `/matchplay/player/{key}/stats` endpoint
- [ ] Implement machine stats aggregation from Matchplay games
- [ ] Create arena-to-machine key mapping logic
- [ ] Add TypeScript types for Matchplay data
- [ ] Add API client functions
- [ ] Create `MatchplaySection` component for player details
- [ ] Add Matchplay rating to team roster display
- [ ] Add Matchplay rating to matchup roster display

### Phase 3: Matchup Page Enhancement
- [ ] Create `/matchplay/team/{key}/stats` endpoint with venue filtering
- [ ] Add Matchplay stats section to matchup page team tabs
- [ ] Filter machine stats to venue-available machines
- [ ] Show team aggregate win % per machine

### Phase 4: Batch Operations
- [ ] Create batch player sync script
- [ ] Add admin endpoint to trigger sync
- [ ] Create review UI for non-exact matches
- [ ] Implement rating cache refresh

---

## Open Questions

1. **Cache Duration**: How long should we cache Matchplay ratings/stats before refreshing?
   - Suggestion: 24 hours for ratings, 1 week for machine stats

2. **Machine Mapping**: How to handle Matchplay arena names that don't match our machine keys?
   - Option A: Manual mapping table
   - Option B: Fuzzy match against `machine_variations.json`
   - Option C: Store both, show Matchplay name if no mapping

3. **Rate Limits**: Need to test Matchplay API rate limits during batch operations

---

## Files to Create/Modify

### New Files
- `api/services/matchplay_client.py` - API client
- `api/services/player_matcher.py` - Matching logic
- `api/routers/matchplay.py` - API endpoints
- `schema/migrations/007_matchplay_integration.sql` - Database schema
- `frontend/components/MatchplaySection.tsx` - Player detail component
- `etl/sync_matchplay_players.py` - Batch sync script

### Modified Files
- `api/main.py` - Register matchplay router
- `api/models/schemas.py` - Add Matchplay schemas
- `frontend/lib/types.ts` - Add Matchplay types
- `frontend/lib/api.ts` - Add Matchplay API functions
- `frontend/app/players/[player_key]/page.tsx` - Add Matchplay section
- `frontend/app/teams/[team_key]/page.tsx` - Add MP rating to roster
- `frontend/app/matchups/page.tsx` - Add team Matchplay stats section

---

*Last Updated: 2025-12-01*
*Status: Planning Complete - Ready for Implementation*
