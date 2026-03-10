# MNP Frontend Design Review

> **Date**: 2026-03-10
> **Reviewer**: Jeremy Collison + Claude
> **Scope**: Full site audit of localhost:3000 (Next.js frontend)
> **Goal**: Identify design improvements, missing data, errors, and formatting issues

---

## Priority Legend

- **P0 — Broken**: Errors, 404s, crashes
- **P1 — Data Issue**: Missing or misleading data
- **P2 — Design Improvement**: UX/UI enhancements
- **P3 — Polish**: Nice-to-have refinements

---

## P0 — Broken

### 1. Weekly Page → 404
**Page**: `/weekly`
**Issue**: Nav link exists but page returns "404: This page could not be found."
**Action**: Either build the page or remove it from the nav bar. A dead nav link is the worst user experience on the site.

### 2. Venue Detail Page → "Error: Failed to fetch"
**Page**: `/venues/8BT` (and likely all venue detail pages when API is unreachable)
**Issue**: Entire page shows only a red error banner with "Error: Failed to fetch" — no venue name, no breadcrumb, no fallback content.
**Action**: Improve error handling to show venue name/header even when the API call for machine lineup fails. Consider separating the Pinball Map API call (which may fail) from the core venue data (which could be statically rendered).

---

## P1 — Data Issues

### 3. Player Machine Stats — %ILE Column Mostly "N/A"
**Page**: `/players/{player_key}` → Machine Statistics table
**Issue**: The %ILE column shows "N/A" for nearly every row. Only scores at the 90th percentile or above get a colored badge (e.g., "98th", "93th"). Everything else — whether it's the 45th percentile or truly missing data — shows the same gray "N/A". This makes the column look broken and provides no useful information for the vast majority of rows.
**Root Causes**:
- `getPercentileStyle()` in `frontend/lib/utils.ts` returns `null` for any percentile below 90th
- Many machines have fewer than 10 league-wide scores, so no percentile thresholds are calculated at all (ETL minimum in `calculate_percentiles.py`)
- Multi-season aggregation may lose percentile data

**Proposed Fix**:
- Always show the numeric percentile when available (e.g., "45th", "72nd", "98th")
- Use color coding across the full range: red (< 25th), gray (25th-49th), white (50th-74th), green (75th-89th), gold (90th+)
- When no percentile data exists (machine has too few scores), show a dash `—` instead of "N/A"
- This makes the distinction clear: a dash means "not enough data", a number means "here's where you rank"

### 4. Chill Flippin Ballers (CFB) — Empty Team Page
**Page**: `/teams/CFB`
**Issue**: Team page shows "Season 23" in the header but has 0 players, no schedule, no machine statistics, and no IPR. The default filter (Seasons 22 + 23) is empty, suggesting CFB only existed in Season 20 or 21.
**Action Items**:
- **Investigate**: Confirm which season(s) CFB was active in. The team should have data in *some* season.
- **All teams should display an Avg IPR on the teams list page**. CFB currently shows a dash `—` for Team IPR.
- **Better empty state**: When a team has no data for the selected seasons, the page should suggest selecting different seasons or auto-detect which seasons have data for this team (e.g., "This team was active in Season 20. Select Season 20 to view their stats.")
- **Consider**: Should inactive teams with no data in recent seasons be hidden by default on the `/teams` list, similar to how `/venues` has a "Show inactive venues" toggle?

### 5. Home Page — MATCHUPS Card Shows "Season 23" Instead of a Count
**Page**: `/` (Home)
**Issue**: The Data Summary card labeled "MATCHUPS" displays "Season 23" as its value. Every other card shows a numeric count (Players: 978, Machines: 379, etc.). This card should show the total number of matchups/matches.
**Action**: Display a match count (e.g., "943") consistent with other cards.

### 6. Machine Detail — Stats Header vs. Filter Mismatch
**Page**: `/machines/Godzilla`
**Issue**: The Machine Statistics card says "Based on data from MNP seasons 20-23" but the active filter chips show "Season 22" and "Season 23". It's unclear whether the stats reflect all seasons or just the filtered ones.
**Action**: The stats note should dynamically reflect the current filter selection, or the stats should always match the applied filters.

### 7. Score Browser — Possible Duplicate Scores
**Page**: `/scores` (loaded with Seasons 22+23)
**Issue**: "4 Aces" shows 4 scores — but it's two pairs of identical player/score/date combos (Ryan Odonnell CA: 701 twice on 2025-11-24, Corbin Stratton: 462 twice on 2025-11-24). This could be a data issue (duplicate ETL load) or could be legitimate (doubles rounds where both games on a machine yield the same score — but that would be very unusual).
**Action**: Investigate whether this is a data duplication bug in the ETL pipeline.

---

## P2 — Design Improvements

### 8. Team Roster — MP Column Always Empty
**Page**: `/teams/ADB` → Team Roster
**Issue**: The "MP" (Matchplay) column shows a dash `—` for every single player on the roster. If Matchplay data is not available for most/all players, the column adds visual noise without providing value.
**Action**: Either populate the Matchplay data for linked players, or hide the column when no data exists. An always-empty column wastes horizontal space and looks like a bug.

### 9. Home Page — Sparse and Underutilized
**Page**: `/`
**Issue**: The home page has a single Data Summary card with 6 stat boxes, then a large empty area below. For a data analysis platform, the landing page could do more to showcase the data and draw users into exploration.
**Possible Enhancements**:
- Recent match results or current week's schedule
- Season standings or leaderboard snippet
- "Top performers this season" or "Most played machines" highlights
- Quick links to current season matchup analysis
- Link to the Live page when matches are in progress

### 10. Live Page — Team Name Truncation
**Page**: `/live`
**Issue**: Several team names are truncated with ellipsis: "The Wrecking...", "Eighteen Ball ...", "Specials Whe...", "Flippin Big Po...", "Little League ...", "Silverball Sla...", "The Trailer Tr...", "Slap Kraken P..."
**Action**: Consider using smaller font sizes for long team names, allowing the cards to use the team's 3-letter abbreviation as a fallback, or making the card grid responsive to accommodate longer names.

### 11. Players List Page — No Default Table
**Page**: `/players`
**Issue**: Before searching, the page shows a Player Spotlight carousel, stat cards, an IPR distribution chart, and a search box — but no browsable list of players. Users must search by name to find anyone. Compare this to the Teams page which shows all teams in a table immediately.
**Possible Enhancement**: Show a paginated/filterable table of all players (sorted by IPR or games played) below the search, so users can browse without knowing a specific name.

### 12. Players List Page — IPR Distribution Chart Lacks Context
**Page**: `/players`
**Issue**: The "Player Distribution by IPR" bar chart shows counts (458, 169, 91, 90, 85, 31) across IPR values 1-6 but doesn't explain what IPR means. A new user has no idea what this chart is telling them.
**Action**: Add a brief explanation or tooltip: "IPR (Individual Player Rating) — number of seasons played. Higher IPR = more experienced player."

---

## P3 — Polish

### 13. Grammar: "1 games"
**Page**: `/players/{player_key}` → Machine Statistics
**Issue**: Machines with a single game show "1 games" (e.g., "1 games ▾" for Aerosmith, Jaws, John Wick, etc.)
**Action**: Pluralize correctly — "1 game" vs. "2 games".

### 14. Percentile Suffix: "93th"
**Page**: `/players/{player_key}` → Machine Statistics
**Issue**: Cactus Canyon shows "93th" — should be "93rd". Similarly, check for "91st", "92nd", "93rd" correctness.
**Action**: Fix ordinal suffix logic (1st, 2nd, 3rd, 4th-20th, 21st, 22nd, 23rd, etc.)

### 15. Venue Detail — No Breadcrumb
**Page**: `/venues/8BT` (when it loads)
**Issue**: Unlike Player and Team detail pages which show breadcrumbs (e.g., "Teams > Admiraballs"), the venue detail page may lack a breadcrumb when it errors. Verify breadcrumb is present in the non-error state.

### 16. Consistent Filter Defaults
**Issue**: Most pages default to "Season 22, Season 23" as the active filters. This is reasonable during Season 23, but may need a mechanism to update automatically as new seasons start (so it's always "current + previous" rather than hardcoded).

---

## Summary Table

| # | Priority | Page | Issue | Type |
|---|----------|------|-------|------|
| 1 | P0 | /weekly | 404 — page doesn't exist | Broken |
| 2 | P0 | /venues/{key} | "Failed to fetch" — no fallback | Broken |
| 3 | P1 | /players/{key} | %ILE column mostly N/A | Data |
| 4 | P1 | /teams/CFB | Empty team, missing IPR | Data |
| 5 | P1 | / (Home) | Matchups shows "Season 23" not count | Data |
| 6 | P1 | /machines/{key} | Stats header vs filter mismatch | Data |
| 7 | P1 | /scores | Possible duplicate scores | Data |
| 8 | P2 | /teams/{key} | MP column always empty | Design |
| 9 | P2 | / (Home) | Sparse landing page | Design |
| 10 | P2 | /live | Team name truncation | Design |
| 11 | P2 | /players | No browsable player table | Design |
| 12 | P2 | /players | IPR chart lacks context | Design |
| 13 | P3 | /players/{key} | "1 games" grammar | Polish |
| 14 | P3 | /players/{key} | "93th" ordinal suffix | Polish |
| 15 | P3 | /venues/{key} | Missing breadcrumb in error state | Polish |
| 16 | P3 | Global | Hardcoded season filter defaults | Polish |
