# IPR Calculator Tool - Planning Document

## Overview

This document outlines the plan for creating an IPR (Individual Player Rating) Calculator tool for the MNP Analytics application. The tool will help players model what match results they need to achieve their next IPR tier.

---

## Understanding IPR and the Rating System

### What is IPR?

IPR (Individual Player Rating) is MNP's 1-6 tier system for categorizing player skill levels. It's derived primarily from MPR (Matchplay Rating), which uses the **Glicko rating system**.

### IPR Tier Distribution

IPR tiers are based on percentiles of the MPR Lower Bound (MPLB) across all players:

| IPR | Percentile Range | Description |
|-----|------------------|-------------|
| 1 | Bottom 30% | Beginner |
| 2 | 30-50% | Developing |
| 3 | 50-65% | Intermediate |
| 4 | 65-80% | Advanced |
| 5 | 80-95% | Expert |
| 6 | Top 5% | Elite |

### MPR Lower Bound (MPLB) Formula

```
MPLB = Rating - (2 × RD)
```

Where:
- **Rating** = Current Matchplay rating (starts at 1500)
- **RD** = Rating Deviation (uncertainty measure, starts at 350)

**Example:**
- New player: MPLB = 1500 - (2 × 350) = 800
- Experienced player with 1550 rating and 30 RD: MPLB = 1550 - (2 × 30) = 1490

---

## The Glicko Rating System

MNP uses the Glicko-1 algorithm via [TournamentUtils](https://github.com/haugstrup/TournamentUtils/blob/master/src/GlickoCalculator.php).

### Key Constants

```
q = ln(10) / 400 ≈ 0.0057565
Default Rating = 1500
Default RD = 350
Minimum RD = 30
c = 14.2694 (RD growth per period of inactivity)
```

### Core Formulas

#### 1. G Function (weight based on opponent's RD)
```
g(RD) = 1 / √(1 + 3q²RD² / π²)
```

This function weights the impact of a game based on how uncertain we are about the opponent's rating. Lower opponent RD = higher weight.

#### 2. Expected Outcome (E)
```
E(rating, opponent_rating, opponent_RD) = 1 / (1 + 10^(-g(RD_opponent) × (rating - opponent_rating) / 400))
```

Returns probability (0-1) of winning against this opponent.

#### 3. D² (variance term)
```
d² = 1 / (q² × Σ(g(RD_j)² × E_j × (1 - E_j)))
```

Sum over all opponents j in the rating period.

#### 4. New RD Calculation
```
new_RD = max(√(1 / (1/RD² + 1/d²)), 30)
```

RD decreases with more games (more certainty). Capped at minimum of 30.

#### 5. New Rating Calculation
```
new_rating = rating + q × new_RD² × Σ(g(RD_j) × (S_j - E_j))
```

Where:
- S_j = actual outcome (1 = win, 0.5 = draw, 0 = loss)
- E_j = expected outcome against opponent j

#### 6. RD Growth Over Time (inactivity)
```
new_RD = min(√(RD² + c²), 350)
```

RD increases when player doesn't compete, up to maximum of 350.

### Group Size Adjustment

For multiplayer games (like pinball groups), the implementation applies:
```
adjustment = √(group_size - 1)
```

This divisor accounts for the fact that in a 4-player group, you're playing against 3 opponents simultaneously.

---

## What the Calculator Needs to Model

### Inputs Required
1. **Current MP Rating** - Player's current Matchplay rating
2. **Current RD** - Player's rating deviation
3. **Current IPR** - Their current tier (1-6)
4. **Target IPR** - The tier they want to achieve

### What to Calculate
1. **Current MPLB** = Rating - (2 × RD)
2. **Target MPLB** = Threshold for target IPR tier
3. **Gap to Target** = Target MPLB - Current MPLB

### Modeling Scenarios

The tool should let users explore:

1. **How many wins against various opponents** would be needed
2. **Impact of reducing RD** through more consistent play
3. **Impact of opponent strength** on rating gains
4. **Time to achieve goal** based on typical match frequency

### Key Insight

There are **two ways to increase MPLB**:
1. **Increase Rating** - Win more games
2. **Decrease RD** - Play more games consistently (even if winning rate stays same)

A player with 1500 rating and 100 RD has MPLB of 1300.
If they play many games and RD drops to 50, MPLB becomes 1400.
No rating change needed!

---

## Technical Implementation Plan

### Backend (FastAPI)

#### New Endpoint: `POST /api/calculator/ipr-projection`

**Request Body:**
```json
{
  "current_rating": 1500,
  "current_rd": 150,
  "opponent_scenarios": [
    {
      "opponent_rating": 1600,
      "opponent_rd": 50,
      "outcome": "win"
    }
  ]
}
```

**Response:**
```json
{
  "current": {
    "rating": 1500,
    "rd": 150,
    "mplb": 1200,
    "ipr": 2
  },
  "projected": {
    "rating": 1520,
    "rd": 145,
    "mplb": 1230,
    "ipr": 2
  },
  "target_ipr_3_gap": 70,
  "scenarios_to_ipr_3": [
    {
      "description": "5 wins vs avg opponents (1500 rating)",
      "projected_rating": 1570,
      "projected_rd": 120,
      "projected_mplb": 1330
    }
  ]
}
```

#### New File: `api/services/glicko_calculator.py`

Python implementation of the Glicko formulas for server-side calculations.

### Frontend (Next.js)

#### New Page: `/app/calculator/page.tsx`

**Features:**
1. **Input Section**
   - Current Rating input (number)
   - Current RD input (number)
   - Current IPR display (calculated)

2. **Scenario Builder**
   - Add opponent matches
   - Select outcome (win/loss/draw)
   - Opponent rating (preset options or custom)
   - Calculate projected results

3. **Results Display**
   - Current vs Projected comparison
   - MPLB progress bar toward next IPR
   - Number of wins needed against various opponents

4. **Visual Aids**
   - IPR tier chart showing thresholds
   - Rating/RD impact visualization
   - "What-if" scenario comparison

### Database Considerations

May need to query:
- IPR tier thresholds (or define as constants)
- Average opponent ratings for reference
- Player's historical match data (optional enhancement)

---

## IPR Threshold Estimation

Since IPR is based on percentiles, we need to either:

1. **Calculate dynamically** from current player pool MPLBs
2. **Use static thresholds** (approximate based on historical data)

### Suggested Approach

Query the database for current MPLB distribution and calculate percentile thresholds:

```sql
WITH player_mplb AS (
  SELECT
    player_key,
    -- We need MP rating and RD from matchplay or calculate from scores
    -- This is a placeholder - actual implementation depends on data available
    estimated_mplb
  FROM players
  WHERE last_seen_season >= 22
)
SELECT
  PERCENTILE_CONT(0.30) WITHIN GROUP (ORDER BY estimated_mplb) as ipr_2_threshold,
  PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY estimated_mplb) as ipr_3_threshold,
  PERCENTILE_CONT(0.65) WITHIN GROUP (ORDER BY estimated_mplb) as ipr_4_threshold,
  PERCENTILE_CONT(0.80) WITHIN GROUP (ORDER BY estimated_mplb) as ipr_5_threshold,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY estimated_mplb) as ipr_6_threshold
FROM player_mplb;
```

**Challenge:** We have IPR (1-6) in our database but not the underlying MP Rating and RD values. Options:
1. Add MP Rating/RD to player data (requires integration with Matchplay API)
2. Use IPR as proxy and let user input their actual MP rating manually
3. Build a "what-if" calculator that doesn't require current player lookup

---

## Data Requirements

### What We Have
- Player names and IPR tiers (1-6)
- Historical match scores
- Win/loss records against opponents

### What We Need (for full implementation)
- Current MP Rating (from matchplay.events)
- Current RD (from matchplay.events)
- OR: Allow manual input of these values

### Matchplay.events Integration

The Matchplay API may provide player ratings. Check:
- `api/services/matchplay_client.py` - existing integration
- `api/routers/matchplay.py` - existing endpoints

Could potentially fetch player MP ratings through existing matchplay integration.

---

## Implementation Phases

### Phase 1: Core Calculator (MVP)
1. Create Glicko calculator service in Python
2. Build simple frontend with manual rating/RD input
3. Calculate single-match impact
4. Show projected rating and MPLB

### Phase 2: Scenario Builder
1. Add multi-match scenario modeling
2. "How many wins to reach IPR X" calculation
3. Preset opponent levels (average player, strong player, etc.)

### Phase 3: Integration
1. Look up player's actual MP rating (if available via Matchplay API)
2. Auto-populate current values based on player search
3. Show historical rating progression

### Phase 4: Advanced Features
1. Recommended opponents for fastest improvement
2. Impact of playing more games (RD reduction)
3. Time-based projections

---

## UI/UX Design Considerations

### Page Layout

```
┌─────────────────────────────────────────────────────────┐
│  IPR Calculator                                         │
├─────────────────────────────────────────────────────────┤
│  Your Current Rating                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ Rating      │ │ RD          │ │ MPLB        │       │
│  │ [1500    ]  │ │ [150     ]  │ │ 1200        │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
│  Current IPR: ●●○○○○ (IPR 2)                           │
│  Target IPR:  [Dropdown: IPR 3 ▼]                      │
│  Gap to IPR 3: 100 MPLB points                         │
├─────────────────────────────────────────────────────────┤
│  Model a Scenario                                       │
│                                                         │
│  Opponent: [Average (1500) ▼] [Custom Rating: ___]     │
│  Their RD: [100] (estimated for active players)        │
│  Outcome:  [Win] [Loss] [Draw]                         │
│                                                         │
│  [+ Add Another Match]                                  │
│                                                         │
│  [Calculate Projection]                                 │
├─────────────────────────────────────────────────────────┤
│  Projection Results                                     │
│                                                         │
│  After 1 win vs 1500-rated opponent:                   │
│  Rating: 1500 → 1515 (+15)                             │
│  RD: 150 → 145 (-5)                                    │
│  MPLB: 1200 → 1225 (+25)                               │
│                                                         │
│  Progress to IPR 3: ████████░░ 80%                     │
│                                                         │
│  Quick Estimates to IPR 3:                              │
│  • ~4 wins vs average players                          │
│  • ~2 wins vs strong players (1700+)                   │
│  • ~8 games played (RD reduction alone)                │
└─────────────────────────────────────────────────────────┘
```

### Components to Use (from existing UI library)

- `Card` - Container for sections
- `Input` - Rating/RD inputs
- `Select` - Opponent presets, target IPR
- `Button` - Add match, calculate
- `Badge` - IPR tier display
- `StatCard` - Current/projected stats
- `PageHeader` - Page title
- Progress indicator (may need new component)

---

## Reference: Glicko PHP Implementation

Source: https://github.com/haugstrup/TournamentUtils/blob/master/src/GlickoCalculator.php

Key methods to implement in Python:
```php
// Constants
q() = log(10) / 400

// G function - weight based on opponent RD
g($rd) = 1 / sqrt(1 + (3 * q² * rd² / π²))

// Expected outcome
E($rating, $opponent_rating, $opponent_rd) {
    $g = g($opponent_rd);
    return 1 / (1 + pow(10, ($g * ($opponent_rating - $rating) / -400)));
}

// New RD calculation
new_rd($rd, $results) {
    // Calculate d² from all results
    // new_rd = sqrt(1 / (1/rd² + 1/d²))
    // Clamp to [30, 350]
}

// New rating calculation
new_rating($rating, $rd, $new_rd, $results) {
    // Sum over all results: g(rd_j) * (outcome - E)
    // new_rating = rating + q * new_rd² * sum
}
```

---

## Files to Create/Modify

### New Files
1. `api/services/glicko_calculator.py` - Python Glicko implementation
2. `api/routers/calculator.py` - API endpoints
3. `frontend/app/calculator/page.tsx` - Calculator page
4. `frontend/lib/glicko.ts` - Client-side Glicko (for instant feedback)

### Modify
1. `api/main.py` - Register new router
2. `frontend/components/Navigation.tsx` - Add Calculator link
3. `frontend/lib/api.ts` - Add calculator API methods
4. `frontend/lib/types.ts` - Add calculator types

---

## Testing Strategy

1. **Unit tests for Glicko calculations**
   - Verify formulas match PHP reference implementation
   - Test edge cases (new player, very low RD, etc.)

2. **Integration tests**
   - API endpoint returns correct projections
   - Multiple scenarios calculate correctly

3. **Manual testing**
   - Compare with actual Matchplay rating changes
   - Validate against known player progressions

---

## Open Questions

1. **Where do users get their MP Rating/RD?**
   - Matchplay.events profile page shows this
   - Could add instructions/link

2. **Should we integrate with Matchplay API for auto-lookup?**
   - Would require user authentication or public API access
   - Check existing matchplay_client.py capabilities

3. **How often do IPR thresholds change?**
   - Based on player pool distribution
   - May want to show "approximate" disclaimer

4. **Should this be player-specific or anonymous?**
   - Anonymous: just enter your numbers
   - Player-specific: look up and track your progress

---

## Resources

- [TournamentUtils Glicko Implementation](https://github.com/haugstrup/TournamentUtils/blob/master/src/GlickoCalculator.php)
- [MNP Ratings Page](https://www.mondaynightpinball.com/ratings)
- [Glicko System Overview](https://en.wikipedia.org/wiki/Glicko_rating_system)
- [Original Glicko Paper](http://www.glicko.net/glicko/glicko.pdf)

---

## Summary

The IPR Calculator will help MNP players understand:
1. Their current standing (MPLB from Rating and RD)
2. How far they are from the next IPR tier
3. What match results would get them there
4. The dual impact of wins (rating) and consistency (RD)

This tool fills a gap in player self-assessment and goal-setting within the MNP ecosystem.
