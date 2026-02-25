# MNP Style Reference

> **Living document** — Update as new design patterns are established.
> Last updated: 2026-02-24

---

## Percentile Color Scale

Used for score percentile badges across all pages (live scores, player stats, machine stats).

| Range | Hex | Name | Usage |
|-------|-----|------|-------|
| 90th+ | `#f59e0b` | Gold/Amber | Elite scores |
| 75–89th | `#a78bfa` | Purple/Violet | Above average |
| 50–74th | `#60a5fa` | Blue | Average |
| < 50th | `#6b7280` | Gray | Below average |

### Percentile Badge Pattern

Colored text on a matching low-opacity background:

```tsx
const style = getPercentileStyle(percentile); // from @/lib/utils
// style = { color: '#f59e0b', label: '92nd' }

<span
  className="text-xs px-1.5 py-0.5 rounded"
  style={{ color: style.color, backgroundColor: `${style.color}22` }}
>
  {style.label}
</span>
```

The `22` hex suffix = ~13% opacity. This pattern is used for all data-driven color badges.

### Percentile Legend

Show when percentile badges appear on a page:

```tsx
<div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
  <span className="font-medium text-gray-400">Percentiles:</span>
  {[
    { color: '#f59e0b', label: '90th+' },
    { color: '#a78bfa', label: '75–89th' },
    { color: '#60a5fa', label: '50–74th' },
    { color: '#6b7280', label: '< 50th' },
  ].map(({ color, label }) => (
    <span key={label} className="flex items-center gap-1">
      <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  ))}
</div>
```

---

## Team Colors

Used in match displays and scoreboards.

| Role | Hex | Name |
|------|-----|------|
| Away team | `#60a5fa` | Blue |
| Home team | `#f87171` | Red |

---

## Bonus Colors

Used in match scoring breakdowns.

| Bonus | Hex | Name |
|-------|-----|------|
| Handicap (HCP) | `#34d399` | Emerald/Green |
| Participation (PAR) | `#a78bfa` | Purple |

---

## Win/Loss Colors

| Result | CSS Variable | Hex (light) |
|--------|-------------|-------------|
| Win | `var(--color-success-500)` | `#22c55e` |
| Loss | `var(--color-error-500)` | `#ef4444` |

---

## Label/Badge Patterns

Small inline labels using the same opacity-background technique as percentile badges:

| Label | Text Color | Background |
|-------|-----------|------------|
| Captain | `#f59e0b` | `#f59e0b33` (20% opacity) |
| Substitute | `#34d399` | `#34d39933` (20% opacity) |
| Player points | `#60a5fa` | `#60a5fa22` (13% opacity) |

```tsx
<span
  className="text-xs font-bold px-1.5 py-0.5 rounded"
  style={{ color: '#f59e0b', backgroundColor: '#f59e0b33' }}
>
  C
</span>
```

---

## Score Display

### Formatting

- Use `font-mono` class for all numeric score values
- Use `formatScore()` from `@/lib/utils` for standard display (3 sig figs)
- Use `fmtScore()` from `@/lib/utils` for compact/abbreviated display (1.2M, 45.3K)

### Points display

Small pill badges for points earned:

```tsx
<span
  className="text-xs font-medium px-1.5 py-0.5 rounded-full"
  style={{ backgroundColor: '#374151', color: '#e5e7eb' }}
>
  {points}
</span>
```

---

## Styling Approach

### When to Use What

| Technique | When |
|-----------|------|
| **CSS variables** (`var(--text-primary)`) | Theme-adaptive colors: text, backgrounds, borders. These change between light and dark mode. |
| **Inline hex styles** | Data-driven colors that stay constant across themes: percentile colors, team colors, bonus colors. |
| **Tailwind classes** | Layout (flex, grid, padding, margin), spacing, typography (`text-sm`, `font-mono`), and standard responsive patterns. |

### Dark Card Pattern (Live pages)

Used for dark-themed data cards regardless of system theme:

```tsx
<div className="rounded-lg" style={{ backgroundColor: '#1f2937' }}>
  <div style={{ backgroundColor: '#111827' }}>Header</div>
  <div style={{ borderBottom: '1px solid #374151' }}>Content</div>
</div>
```

### Theme-Aware Card Pattern (Standard pages)

Used for cards that respect light/dark mode:

```tsx
<div
  className="border rounded-lg p-3"
  style={{ borderColor: 'var(--border)', backgroundColor: 'var(--card-bg-secondary)' }}
>
  Content
</div>
```

---

## CSS Variables Reference

Defined in `frontend/app/globals.css`. Key variables:

### Text
- `--text-primary` — Headings, primary content
- `--text-secondary` — Body text, descriptions
- `--text-muted` — Labels, captions, less important text
- `--text-link` — Link text color
- `--text-link-hover` — Link hover color

### Backgrounds
- `--background` — Page background
- `--card-bg` — Card/container background
- `--card-bg-secondary` — Nested/secondary card background

### Borders
- `--border` — Standard border
- `--border-light` — Subtle border

### Table
- `--table-header-bg` — Table header row
- `--table-row-hover` — Row hover state
- `--table-row-stripe` — Alternating row background
- `--table-border` — Table dividers

---

## Shared Utility Functions

All in `frontend/lib/utils.ts`:

| Function | Purpose |
|----------|---------|
| `getPercentileStyle(pct)` | Returns `{ color, label }` for a percentile value |
| `fmtScore(score)` | Abbreviated score format (45.3K, 1.2M) |
| `formatScore(score)` | Standard score format with locale separators |
| `cn(...classes)` | Tailwind class merging utility |
