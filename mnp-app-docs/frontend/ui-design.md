# Frontend UI/UX Design

## Overview

The MNP Analyzer frontend is a mobile-first Progressive Web App (PWA) built with Next.js 14 and React. The design prioritizes:

1. **Speed**: < 2 second initial load, instant navigation
2. **Simplicity**: Maximum 2-3 taps to any information
3. **Clarity**: Large touch targets, readable text, clear hierarchy
4. **Offline**: Core features work without internet connection

## Design System

### Color Palette

**Primary Colors:**
- Primary Blue: `#2563EB` (actions, links, highlights)
- Primary Dark: `#1E40AF` (hover states)
- Primary Light: `#DBEAFE` (backgrounds)

**Secondary Colors:**
- Success Green: `#10B981` (positive indicators)
- Warning Yellow: `#F59E0B` (caution)
- Danger Red: `#EF4444` (negative indicators)

**Neutral Colors (Light Mode):**
- Text Primary: `#111827` (main text)
- Text Secondary: `#4B5563` (supporting text)
- Text Muted: `#6B7280` (tertiary text)
- Background: `#F9FAFB` (main background)
- Card Background: `#FFFFFF` (cards)
- Card Background Secondary: `#F9FAFB` (footers, secondary areas)
- Border: `#E5E7EB` (dividers, borders)

**Neutral Colors (Dark Mode):**
- Text Primary: `#F9FAFB` (main text)
- Text Secondary: `#D1D5DB` (supporting text)
- Text Muted: `#9CA3AF` (tertiary text)
- Background: `#0A0A0A` (main background)
- Card Background: `#171717` (cards)
- Card Background Secondary: `#1F1F1F` (footers, secondary areas)
- Border: `#2A2A2A` (dividers, borders)

**Percentile Color Scale:**
- 90-100%: `#10B981` (Excellent - Green)
- 75-89%: `#3B82F6` (Good - Blue)
- 50-74%: `#F59E0B` (Average - Yellow)
- 25-49%: `#F97316` (Below Average - Orange)
- 0-24%: `#EF4444` (Poor - Red)

### Typography

**Font Family:**
- Primary: `Inter` (system fallback: `-apple-system, BlinkMacSystemFont, "Segoe UI"`)
- Monospace: `JetBrains Mono` (for scores and stats)

**Font Sizes:**
- Heading 1: `2rem` (32px) - Page titles
- Heading 2: `1.5rem` (24px) - Section headers
- Heading 3: `1.25rem` (20px) - Subsections
- Body Large: `1.125rem` (18px) - Emphasis
- Body: `1rem` (16px) - Default
- Body Small: `0.875rem` (14px) - Supporting text
- Caption: `0.75rem` (12px) - Labels, meta info

**Font Weights:**
- Regular: 400 (body text)
- Medium: 500 (emphasis)
- Semibold: 600 (headings, buttons)
- Bold: 700 (important numbers)

### Spacing

Base unit: `4px` (0.25rem)

- xs: `4px` (0.25rem)
- sm: `8px` (0.5rem)
- md: `16px` (1rem)
- lg: `24px` (1.5rem)
- xl: `32px` (2rem)
- 2xl: `48px` (3rem)

### Touch Targets

- Minimum touch target: `44px × 44px`
- Button height: `48px`
- Icon buttons: `48px × 48px`
- List items: `56px` minimum height

### Shadows

```css
shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05)
shadow: 0 1px 3px rgba(0, 0, 0, 0.1)
shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1)
shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1)
```

### Border Radius

- sm: `4px` (inputs, small cards)
- md: `8px` (buttons, cards)
- lg: `12px` (large cards)
- full: `9999px` (pills, badges)

## Layout Structure

### Mobile Layout (320px - 768px)

```
┌─────────────────────────────┐
│ Header (sticky)             │ 64px
├─────────────────────────────┤
│                             │
│                             │
│    Main Content Area        │
│    (scrollable)             │
│                             │
│                             │
├─────────────────────────────┤
│ Bottom Nav (optional)       │ 64px
└─────────────────────────────┘
```

### Tablet/Desktop Layout (768px+)

```
┌─────────────────────────────────────┐
│ Header (sticky)                     │ 64px
├─────────────┬───────────────────────┤
│             │                       │
│  Sidebar    │   Main Content        │
│  (optional) │   (scrollable)        │
│             │                       │
│             │                       │
└─────────────┴───────────────────────┘
```

## Screen Designs

### 1. Home Screen

**Purpose**: Quick access to search and common tasks

**Layout:**
```
┌─────────────────────────────────────┐
│ ≡  MNP Analyzer              [⚙]   │ Header
├─────────────────────────────────────┤
│                                     │
│  [Venue Selector]                   │ Sticky context
│  📍 I'm at: [4Bs Tavern      ▼]    │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  [Search Bar]                       │ Primary action
│  🔍 Search player or team...        │
│                                     │
│  ─────────────────────────────────  │
│                                     │
│  Quick Access:                      │ Action cards
│  ┌─────────────────────────────┐   │
│  │ 📊 My Stats                 │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 🎯 Team Intel               │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 🎮 Machine Lookup           │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ ⚔️  Compare Players          │   │
│  └─────────────────────────────┘   │
│                                     │
│  Recent Matches:                    │ Quick links
│  • Week 3: ADB vs TBT              │
│  • Week 2: NMC vs JMF              │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Sticky header with hamburger menu and settings
- Venue selector (dropdown with search)
- Search bar with autocomplete
- Action cards (4 main features)
- Recent matches list

---

### 2. Search Results

**Purpose**: Display player/team search results

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  Search Results                   │
├─────────────────────────────────────┤
│ 🔍 scott                       [×]  │
│                                     │
│ Found 3 results:                    │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Scott Helgason             IPR 6│ │
│ │ Admiraballs • 145 games         │ │
│ │ 📊 85th %ile median             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Scott Lee WA               IPR 5│ │
│ │ Admiraballs • 89 games          │ │
│ │ 📊 72nd %ile median             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Scott Anderson             IPR 4│ │
│ │ NMC • 56 games                  │ │
│ │ 📊 68th %ile median             │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Back navigation
- Search input with clear button
- Result cards with key stats
- Tappable cards navigate to detail view

---

### 3. Player Detail Screen

**Purpose**: Comprehensive player statistics

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  Scott Helgason                   │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │ Player header
│ │ Scott Helgason            IPR 6 │ │
│ │ Admiraballs (ADB)               │ │
│ │ 📍 Home: Jupiter's Tap          │ │
│ │                                 │ │
│ │ Season 22 Stats:                │ │
│ │ • 48 games played               │ │
│ │ • 85th %ile median              │ │
│ │ • 35 machines played            │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [At Venue: 4Bs Tavern ▼]           │ Filters
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Best Machines at This Venue:        │ Key insight
│ ┌─────────────────────────────────┐ │
│ │ 🥇 Medieval Madness             │ │
│ │    92nd %ile • 8 games          │ │
│ │    Median: 32.5M                │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🥈 Twilight Zone                │ │
│ │    86th %ile • 6 games          │ │
│ │    Median: 195M                 │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🥉 James Bond 007               │ │
│ │    78th %ile • 5 games          │ │
│ │    Median: 218M                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [View All Machines →]               │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Performance Breakdown:              │ Stats
│ • Home games: 84th %ile            │
│ • Away games: 86th %ile            │
│ • Singles: 85th %ile               │
│ • Doubles: 85th %ile               │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Player header card with avatar placeholder
- Venue filter dropdown
- Top 3 machines ranked by percentile
- "View All" expansion
- Performance breakdown stats

---

### 4. Machine Picker (Player View)

**Purpose**: Help player choose best machine

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  Machine Picker                   │
├─────────────────────────────────────┤
│ Player: Scott Helgason              │
│ Venue: 4Bs Tavern                   │
│                                     │
│ [All | Singles | Doubles]           │ Round filter
│                                     │
│ Your Best Picks:                    │
│ ┌─────────────────────────────────┐ │
│ │ 🥇 Medieval Madness             │ │
│ │    92nd %ile • 8 games      [→]│ │
│ │    ▓▓▓▓▓▓▓▓▓░  92%             │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🥈 Twilight Zone                │ │
│ │    86th %ile • 6 games      [→]│ │
│ │    ▓▓▓▓▓▓▓▓▓░  86%             │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🥉 James Bond 007               │ │
│ │    78th %ile • 5 games      [→]│ │
│ │    ▓▓▓▓▓▓▓▓░░  78%             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Other Available Machines:           │
│ ┌───────────────────────────────┐   │
│ │ Godzilla         68% • 4 [→] │   │
│ ├───────────────────────────────┤   │
│ │ Guardians        64% • 3 [→] │   │
│ ├───────────────────────────────┤   │
│ │ Indiana Jones    58% • 2 [→] │   │
│ ├───────────────────────────────┤   │
│ │ Taxi             51% • 5 [→] │   │
│ └───────────────────────────────┘   │
│                                     │
│ [Sort: Best %ile ▼]  [Filter: All]  │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Context header (player + venue)
- Round type filter tabs
- Top 3 picks with visual ranking
- Progress bars for percentile
- Scrollable list of other machines
- Sort and filter controls
- Tap any machine for details

---

### 5. Machine Detail Screen

**Purpose**: Detailed performance on specific machine

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  Medieval Madness                 │
├─────────────────────────────────────┤
│ at 4Bs Tavern                       │
│                                     │
│ Your Performance:                   │ Player stats
│ ┌─────────────────────────────────┐ │
│ │ 92nd Percentile                 │ │
│ │                                 │ │
│ │ • Games: 8                      │ │
│ │ • Median: 32.5M                 │ │
│ │ • Best: 78.0M (99th %ile)       │ │
│ │ • Worst: 18.2M (52nd %ile)      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Score Distribution:                 │ Chart
│ ┌─────────────────────────────────┐ │
│ │      ╱                          │ │
│ │    ╱                            │ │
│ │  ╱                              │ │
│ │╱_____________________________   │ │
│ │ 0%  25%  50%  75%  95%         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Score Targets:                      │ Benchmarks
│ ├─ 50th: 18.5M                     │
│ ├─ 75th: 28.0M                     │
│ ├─ 90th: 42.0M  ← You are here    │
│ └─ 95th: 55.0M                     │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Your Game History:                  │ History
│ ┌───────────────────────────────┐   │
│ │ 78.0M  99%  Week 3  01/15    │   │
│ ├───────────────────────────────┤   │
│ │ 42.5M  94%  Week 2  01/08    │   │
│ ├───────────────────────────────┤   │
│ │ 35.2M  88%  Week 1  01/01    │   │
│ └───────────────────────────────┘   │
│                                     │
│ [View All Scores →]                 │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Machine name header with venue
- Player performance summary card
- Score distribution chart (simplified for mobile)
- Score target benchmarks with indicator
- Scrollable game history
- Expandable full history view

---

### 6. Team Intel Screen

**Purpose**: Understand opponent team strategy

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  The B Team (TBT)                 │
├─────────────────────────────────────┤
│ Home: 4Bs Tavern                    │
│                                     │
│ [Home | Away]  [Singles | Doubles]  │ Filters
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Favorite Picks (Home Singles):      │ Machine picks
│ ┌─────────────────────────────────┐ │
│ │ 1. Medieval Madness             │ │
│ │    8/10 picks • 75% win rate    │ │
│ │    Avg: 25M • 18 pts earned     │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 2. Twilight Zone                │ │
│ │    6/10 picks • 67% win rate    │ │
│ │    Avg: 172M • 14 pts earned    │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 3. James Bond 007               │ │
│ │    5/10 picks • 60% win rate    │ │
│ │    Avg: 195M • 11 pts earned    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Top Players:                        │ Roster
│ ┌─────────────────────────────────┐ │
│ │ Campbell Hancock          IPR 6 │ │
│ │ 12 games • 88th %ile median     │ │
│ │ Best: MM, TZ, 007               │ │
│ │ [View Stats →]                  │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ David Chernicoff          IPR 5 │ │
│ │ 11 games • 76th %ile median     │ │
│ │ Best: Godzilla, JW, PULP        │ │
│ │ [View Stats →]                  │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [View Full Roster →]                │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Team header with home venue
- Filter tabs for home/away and round type
- Machine pick ranking with stats
- Player cards with top machines
- Expandable full roster view

---

### 7. Player Comparison Screen

**Purpose**: Compare two players for matchup strategy

**Layout:**
```
┌─────────────────────────────────────┐
│ ←  Player Comparison                │
├─────────────────────────────────────┤
│                                     │
│ [Search Player 1...]                │ Selection
│ Scott Helgason  [×]                 │
│                                     │
│            VS                       │
│                                     │
│ [Search Player 2...]                │
│ Matthew Greene  [×]                 │
│                                     │
│ Machine: [Medieval Madness ▼]       │
│ Venue: [4Bs Tavern ▼]              │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Matchup Analysis:                   │ Comparison
│                                     │
│ ┌───────────────┬───────────────┐   │
│ │ Scott H.      │ Matthew G.    │   │
│ │ IPR 6         │ IPR 5         │   │
│ ├───────────────┼───────────────┤   │
│ │ 92nd %ile     │ 78th %ile     │   │
│ │ ████████████  │ ███████░░     │   │
│ ├───────────────┼───────────────┤   │
│ │ 8 games       │ 6 games       │   │
│ ├───────────────┼───────────────┤   │
│ │ 32.5M median  │ 25.8M median  │   │
│ ├───────────────┼───────────────┤   │
│ │ 78.0M best    │ 42.0M best    │   │
│ └───────────────┴───────────────┘   │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ ⚡ Advantage: Scott Helgason    │ │
│ │    +14 percentile points        │ │
│ │    Confidence: High (8+ games) │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ─────────────────────────────────── │
│                                     │
│ Head-to-Head Record:                │ H2H stats
│ • 3 games together on this machine │
│ • Scott wins: 2 (67%)              │
│ • Matthew wins: 1 (33%)            │
│                                     │
└─────────────────────────────────────┘
```

**Components:**
- Player search/select inputs
- VS divider
- Machine and venue filters
- Side-by-side comparison table
- Advantage indicator
- Head-to-head history

---

## Component Library

### Buttons

**Primary Button:**
```tsx
<button className="
  bg-blue-600 text-white
  px-6 py-3 rounded-lg
  font-semibold
  hover:bg-blue-700 active:bg-blue-800
  transition-colors
  min-h-[48px]
">
  Primary Action
</button>
```

**Secondary Button:**
```tsx
<button className="
  bg-white text-blue-600 border-2 border-blue-600
  px-6 py-3 rounded-lg
  font-semibold
  hover:bg-blue-50 active:bg-blue-100
  transition-colors
  min-h-[48px]
">
  Secondary Action
</button>
```

**Icon Button:**
```tsx
<button className="
  w-12 h-12 rounded-full
  flex items-center justify-center
  hover:bg-gray-100 active:bg-gray-200
  transition-colors
">
  <Icon size={24} />
</button>
```

### Cards

**Basic Card:**
```tsx
<div className="
  bg-white rounded-lg shadow-md
  p-4 border border-gray-200
  hover:shadow-lg transition-shadow
">
  Card Content
</div>
```

**Machine Card (List Item):**
```tsx
<div className="
  bg-white rounded-lg p-4
  border-l-4 border-green-500
  hover:bg-gray-50 active:bg-gray-100
  cursor-pointer
">
  <div className="flex justify-between items-center">
    <div>
      <h3 className="font-semibold text-lg">Medieval Madness</h3>
      <p className="text-gray-600 text-sm">92nd %ile • 8 games</p>
    </div>
    <ChevronRight className="text-gray-400" />
  </div>
</div>
```

**Entity Card (Grid Item):**
Used for displaying venues, teams, or similar entities in a grid layout.
```tsx
<Card variant="interactive" href="/venues/T4B">
  <Card.Content className="p-5">
    <div className="space-y-3">
      {/* Entity Name */}
      <h3 className="text-lg font-semibold truncate" style={{ color: 'var(--text-primary)' }}>
        4Bs Tavern
      </h3>

      {/* Stats Row */}
      <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--text-secondary)' }}>
        <div className="flex items-center gap-1.5">
          <Icon className="w-4 h-4" />
          <span>17 machines</span>
        </div>
      </div>

      {/* Related Items Section */}
      <div className="pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="text-xs font-medium mb-1.5 uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
          Home Teams
        </div>
        <div className="flex flex-wrap gap-1.5">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                style={{ backgroundColor: 'var(--card-bg-secondary)', color: 'var(--text-secondary)' }}>
            Team Name
          </span>
        </div>
      </div>
    </div>
  </Card.Content>
</Card>
```

**Grid Layout for Entity Cards:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map((item) => (
    <EntityCard key={item.key} item={item} />
  ))}
</div>
```

### Badges

**Percentile Badge:**
```tsx
<span className="
  inline-flex items-center
  px-3 py-1 rounded-full
  text-sm font-medium
  bg-green-100 text-green-800
">
  92nd %ile
</span>
```

Color mapping:
- Green: 90-100%
- Blue: 75-89%
- Yellow: 50-74%
- Orange: 25-49%
- Red: 0-24%

### Progress Bars

**Percentile Progress Bar:**
```tsx
<div className="w-full bg-gray-200 rounded-full h-3">
  <div
    className="bg-green-500 h-3 rounded-full transition-all"
    style={{ width: '92%' }}
  />
</div>
```

### Input Fields

**Search Input:**
```tsx
<div className="relative">
  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
  <input
    type="text"
    className="
      w-full pl-10 pr-4 py-3
      border-2 border-gray-300 rounded-lg
      focus:border-blue-500 focus:outline-none
      text-base
    "
    placeholder="Search..."
  />
</div>
```

**Dropdown:**
```tsx
<select className="
  w-full px-4 py-3
  border-2 border-gray-300 rounded-lg
  focus:border-blue-500 focus:outline-none
  text-base
  appearance-none
  bg-white
">
  <option>Option 1</option>
  <option>Option 2</option>
</select>
```

### Loading States

**Skeleton Card:**
```tsx
<div className="bg-white rounded-lg p-4 animate-pulse">
  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
</div>
```

**Spinner:**
```tsx
<div className="flex justify-center items-center p-8">
  <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
</div>
```

### Empty States

```tsx
<div className="flex flex-col items-center justify-center p-12 text-center">
  <EmptyIcon className="w-16 h-16 text-gray-300 mb-4" />
  <h3 className="text-lg font-semibold text-gray-900 mb-2">
    No results found
  </h3>
  <p className="text-gray-600">
    Try adjusting your filters or search terms
  </p>
</div>
```

## Navigation

### Header Navigation

**Mobile Header:**
- Hamburger menu (left)
- Page title (center)
- Action icon (right) - settings, filter, etc.
- Sticky on scroll
- Height: 64px

**Menu Items:**
- Home
- My Stats (saved player)
- Favorites
- Settings
- About / Help

### Bottom Navigation (Optional)

For most-used features:
- Home
- Search
- Favorites
- Profile/Stats

## Responsive Breakpoints

```css
/* Mobile: 320px - 639px (default) */
/* Tablet: 640px - 1023px */
@media (min-width: 640px) { ... }

/* Desktop: 1024px+ */
@media (min-width: 1024px) { ... }
```

## Animations & Transitions

**Page Transitions:**
- Slide in from right (navigate forward)
- Slide in from left (navigate back)
- Duration: 200ms
- Easing: `ease-out`

**Micro-interactions:**
- Button press: Scale down to 0.98
- Card hover: Lift with shadow
- Toggle: Smooth slide transition
- Expand/collapse: Height animation with ease

**Performance:**
- Use `transform` and `opacity` for animations (GPU-accelerated)
- Avoid animating `height`, `width`, `top`, `left` directly
- Use `will-change` sparingly

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast:**
- Text on background: minimum 4.5:1 ratio
- Large text: minimum 3:1 ratio
- Interactive elements: clearly distinguishable

**Keyboard Navigation:**
- All interactive elements accessible via keyboard
- Visible focus indicators
- Logical tab order

**Screen Reader Support:**
- Semantic HTML elements
- ARIA labels where needed
- Alternative text for icons

**Touch Targets:**
- Minimum 44px × 44px
- Adequate spacing between elements

## Performance Optimizations

### Image Loading
- Lazy load images below fold
- Use WebP with fallbacks
- Responsive image sizes
- Placeholder blur effect

### Code Splitting
- Route-based splitting
- Component lazy loading
- Dynamic imports for heavy features

### Caching Strategy
- Cache API responses (TanStack Query)
- Service worker for offline support
- Static assets cached indefinitely
- API data cached with TTL

## PWA Features

### Install Prompt
- Show "Add to Home Screen" prompt after 2+ visits
- Custom install banner
- App icon and splash screen

### Offline Support
- Core features work offline
- Cached player/team data
- "You're offline" indicator
- Sync when reconnected

### Push Notifications (Future)
- Match reminders
- New opponent intel
- Score milestone achievements

---

## Dark Mode Support

The application supports automatic dark mode based on system preferences using CSS custom properties (CSS variables) defined in `frontend/app/globals.css`.

### Implementation Strategy

Dark mode is implemented using:
1. **CSS Custom Properties**: All colors are defined as CSS variables in `:root` with automatic overrides in `@media (prefers-color-scheme: dark)`
2. **Inline Styles**: Components use `style={{ color: 'var(--text-primary)' }}` to reference CSS variables
3. **Automatic Detection**: No manual toggle needed - follows system preference via `prefers-color-scheme` media query

### Available CSS Variables

**Text Colors:**
- `--text-primary`: Main heading and body text
- `--text-secondary`: Supporting text, descriptions
- `--text-muted`: Tertiary text, labels, placeholders
- `--text-link`: Clickable links
- `--text-link-hover`: Link hover state

**Background Colors:**
- `--background`: Page background
- `--card-bg`: Card/component backgrounds
- `--card-bg-secondary`: Footer areas, secondary backgrounds
- `--table-header-bg`: Table header background
- `--table-row-hover`: Table row hover state

**Border Colors:**
- `--border`: Primary borders
- `--border-light`: Subtle borders
- `--table-border`: Table dividers

**Form Elements:**
- `--input-bg`: Input/select backgrounds
- `--input-border`: Input border color
- `--input-disabled-bg`: Disabled input background

### Usage in Components

```tsx
// Use CSS variables for colors
<h1 style={{ color: 'var(--text-primary)' }}>Title</h1>
<p style={{ color: 'var(--text-secondary)' }}>Description</p>
<div style={{ backgroundColor: 'var(--card-bg)', borderColor: 'var(--border)' }}>
  Content
</div>
```

### Best Practices

1. **Never use hardcoded gray colors** like `text-gray-900` or `bg-white` for text/backgrounds
2. **Always use CSS variables** for colors that should adapt to dark mode
3. **Accent colors can remain static** (blue-600, green-500, red-500) as they work in both modes
4. **Test both modes** by toggling system appearance settings

### Components Updated for Dark Mode

All components in `frontend/components/ui/` have been updated:
- Card, CardHeader, CardTitle, CardContent, CardFooter
- PageHeader
- StatCard
- Table, TableHeader, TableBody, TableRow, TableHead, TableCell
- Input, Select
- MultiSelect, MultiSelectButtons, MultiSelectDropdown
- Tabs, TabsList, TabsTrigger, TabsContent
- Collapsible
- FilterPanel
- EmptyState
- LoadingSpinner
- Navigation

### Navigation Bar Design

The navigation bar uses **fixed hex colors** (not CSS variables) to maintain a consistent dark header in both light and dark modes:

```tsx
// Navigation.tsx - Uses explicit hex colors, NOT CSS variables
<nav style={{ backgroundColor: '#111827', color: '#ffffff' }}>
  <span style={{ color: '#ffffff' }}>MNP Analyzer</span>
  <Link style={{ color: isActive ? '#ffffff' : '#d1d5db' }}>...</Link>
</nav>
```

**Rationale:**
- The navigation should always have a dark background with white text
- Using CSS variables would cause the nav to adapt to light/dark mode (undesired)
- Hardcoded Tailwind classes like `bg-gray-900` can be overridden by CSS variable definitions
- Inline styles with explicit hex values ensure consistent appearance regardless of color scheme

---

## Filter Design Guidelines

### Standard Filter Pattern

All pages with filters should follow this consistent pattern:

1. **Use FilterPanel Component**: Wrap all filters in a collapsible `FilterPanel`
   - Always set `collapsible={true}` for space efficiency
   - Track `activeFilterCount` to show badge
   - Provide `onClearAll` to reset filters

2. **Use Dropdown Variants for Multi-Select**: For space efficiency, use `variant="dropdown"` on:
   - `SeasonMultiSelect` - dropdown with checkboxes
   - `RoundMultiSelect` - dropdown with checkboxes
   - `VenueSelect` or `VenueMultiSelect` - standard select or multi-select dropdown

3. **Consistent Sizing**: All dropdowns have `h-[38px]` height for visual alignment

### Example Implementation

```tsx
import { FilterPanel } from '@/components/ui';
import { SeasonMultiSelect } from '@/components/SeasonMultiSelect';
import { VenueSelect } from '@/components/VenueMultiSelect';
import { RoundMultiSelect } from '@/components/RoundMultiSelect';

// Calculate active filters
const activeFilterCount =
  (selectedSeasons.length > 0 ? 1 : 0) +
  (selectedVenue ? 1 : 0) +
  (selectedRounds.length < 4 ? 1 : 0);

function clearFilters() {
  setSelectedSeasons([]);
  setSelectedVenue('');
  setSelectedRounds([1, 2, 3, 4]);
}

<FilterPanel
  title="Filters"
  collapsible={true}
  activeFilterCount={activeFilterCount}
  showClearAll={activeFilterCount > 0}
  onClearAll={clearFilters}
>
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    <SeasonMultiSelect
      value={selectedSeasons}
      onChange={setSelectedSeasons}
      availableSeasons={availableSeasons}
      variant="dropdown"
    />
    <VenueSelect
      value={selectedVenue}
      onChange={setSelectedVenue}
      venues={venues}
    />
    <RoundMultiSelect
      value={selectedRounds}
      onChange={setSelectedRounds}
      variant="dropdown"
    />
  </div>
</FilterPanel>
```

### Available Filter Components

| Component | Single/Multi | Variants | Usage |
|-----------|--------------|----------|-------|
| `SeasonMultiSelect` | Multi | `buttons`, `dropdown` | Filter by seasons |
| `SeasonSelect` | Single | dropdown only | Select one season |
| `VenueMultiSelect` | Multi | dropdown only | Filter by venues |
| `VenueSelect` | Single | dropdown only | Select one venue |
| `RoundMultiSelect` | Multi | `buttons`, `dropdown` | Filter by rounds |

### When to Use Button vs Dropdown Variant

- **Dropdown (recommended)**: Use for most cases, especially when:
  - Space is limited
  - Many options available (>5)
  - Options have long labels
  - Consistency with other filters on page

- **Buttons**: Use only when:
  - Few options (≤5) that fit in a single row
  - Quick visual scanning is important
  - The page has ample horizontal space

---

**Design Version**: 1.2
**Last Updated**: 2026-01-14
**Status**: Dark mode implemented, Filter guidelines added
**Figma Link**: TBD
