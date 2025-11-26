# MNP Analyzer Design System

**Version:** 1.0
**Last Updated:** 2025-11-26
**Status:** In Development

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Color System](#color-system)
4. [Typography](#typography)
5. [Spacing & Layout](#spacing--layout)
6. [Components](#components)
7. [Patterns](#patterns)
8. [Implementation Plan](#implementation-plan)

---

## Overview

This design system provides a unified visual language and component library for the MNP Analyzer web application. It's built on top of **Tailwind CSS v4** and **React 19**, emphasizing:

- **Consistency**: Reusable components ensure uniform appearance across all pages
- **Accessibility**: WCAG 2.1 AA compliance for interactive elements
- **Performance**: Lightweight components optimized for fast rendering
- **Maintainability**: Centralized design tokens make updates easy

### Current Tech Stack

- **Framework:** Next.js 16 (App Router)
- **UI Library:** React 19
- **Styling:** Tailwind CSS v4 (PostCSS)
- **Language:** TypeScript 5

---

## Design Principles

### 1. Data-First Design
MNP is a data-heavy application. Design should enhance readability and comprehension:
- **Clear visual hierarchy** for tables and lists
- **Scannable layouts** with consistent spacing
- **Meaningful use of color** to highlight important data (high scores, rankings, etc.)

### 2. Responsive & Mobile-Friendly
All components must work across devices:
- **Mobile-first approach** with progressive enhancement
- **Breakpoints:** sm (640px), md (768px), lg (1024px)
- Tables should scroll horizontally on mobile when necessary

### 3. Performance-Conscious
Fast page loads are critical:
- **Minimal JavaScript** - leverage server components where possible
- **No unnecessary animations** - transitions only where they enhance UX
- **Efficient re-renders** - memoization for expensive operations

### 4. Accessible by Default
Every component should be usable by everyone:
- **Keyboard navigation** support
- **Screen reader** friendly markup
- **Sufficient color contrast** (WCAG AA minimum)
- **Focus indicators** on all interactive elements

---

## Color System

### Brand Colors

**Primary Blue** (Interactive elements, links, active states)
```css
--color-primary-50: #eff6ff;
--color-primary-100: #dbeafe;
--color-primary-500: #3b82f6;  /* Main brand color */
--color-primary-600: #2563eb;  /* Hover/active states */
--color-primary-700: #1d4ed8;
```

**Neutral Grays** (Text, backgrounds, borders)
```css
--color-gray-50: #f9fafb;   /* Light backgrounds */
--color-gray-100: #f3f4f6;  /* Card backgrounds */
--color-gray-200: #e5e7eb;  /* Borders */
--color-gray-300: #d1d5db;
--color-gray-500: #6b7280;  /* Secondary text */
--color-gray-600: #4b5563;  /* Body text */
--color-gray-700: #374151;
--color-gray-900: #111827;  /* Headings, dark backgrounds */
```

### Semantic Colors

**Success** (Positive stats, wins)
```css
--color-success-50: #f0fdf4;
--color-success-500: #22c55e;
--color-success-700: #15803d;
```

**Warning** (Alerts, important notices)
```css
--color-warning-50: #fefce8;
--color-warning-500: #eab308;
--color-warning-700: #a16207;
```

**Error** (Errors, losses)
```css
--color-error-50: #fef2f2;
--color-error-500: #ef4444;
--color-error-700: #b91c1c;
```

**Info** (Informational messages)
```css
--color-info-50: #f0f9ff;
--color-info-500: #0ea5e9;
--color-info-700: #0369a1;
```

### Theme Support

Support for light and dark modes via CSS custom properties:

```css
:root {
  --background: #ffffff;
  --foreground: #171717;
  --card-bg: #ffffff;
  --border: #e5e7eb;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: #0a0a0a;
    --foreground: #ededed;
    --card-bg: #1a1a1a;
    --border: #2a2a2a;
  }
}
```

---

## Typography

### Font Families

**Sans-Serif** (Primary - UI text)
- **Family:** Geist Sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif
- **Usage:** Headings, body text, UI elements

**Monospace** (Secondary - code, technical data)
- **Family:** Geist Mono, "SF Mono", Monaco, "Courier New", monospace
- **Usage:** Machine keys, player keys, technical identifiers

### Type Scale

| Element | Tailwind Class | Size | Line Height | Weight |
|---------|---------------|------|-------------|--------|
| **H1 (Page Title)** | `text-3xl font-bold` | 30px | 1.2 | 700 |
| **H2 (Section)** | `text-2xl font-semibold` | 24px | 1.3 | 600 |
| **H3 (Subsection)** | `text-xl font-semibold` | 20px | 1.4 | 600 |
| **H4 (Card Title)** | `text-lg font-medium` | 18px | 1.5 | 500 |
| **Body Large** | `text-base` | 16px | 1.6 | 400 |
| **Body** | `text-sm` | 14px | 1.5 | 400 |
| **Small** | `text-xs` | 12px | 1.4 | 400 |
| **Label** | `text-sm font-medium` | 14px | 1.4 | 500 |

### Text Colors

| Use Case | Tailwind Class | Hex |
|----------|---------------|-----|
| Primary text | `text-gray-900` | #111827 |
| Secondary text | `text-gray-600` | #4b5563 |
| Muted text | `text-gray-500` | #6b7280 |
| Link (default) | `text-blue-600` | #2563eb |
| Link (hover) | `text-blue-700` | #1d4ed8 |

---

## Spacing & Layout

### Spacing Scale

Use Tailwind's default spacing scale (1 unit = 0.25rem = 4px):

| Name | Tailwind | Pixels | Usage |
|------|----------|--------|-------|
| **Tight** | `space-y-2`, `gap-2` | 8px | Compact lists, form fields |
| **Normal** | `space-y-4`, `gap-4` | 16px | Default vertical rhythm |
| **Relaxed** | `space-y-6`, `gap-6` | 24px | Page sections |
| **Loose** | `space-y-8`, `gap-8` | 32px | Major page divisions |

### Container Widths

```css
max-w-7xl  /* 1280px - Default page container */
max-w-4xl  /* 896px - Narrow content (forms, articles) */
max-w-full /* 100% - Full-width tables, charts */
```

### Grid Patterns

**Responsive Card Grid:**
```tsx
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
```

**Two-Column Layout:**
```tsx
className="grid grid-cols-1 md:grid-cols-2 gap-6"
```

**Form Layout:**
```tsx
className="grid grid-cols-1 md:grid-cols-3 gap-4"
```

---

## Components

### Component Library Structure

```
/frontend/components/ui/
├── Card.tsx              # Container component
├── Table.tsx             # Data table with sorting
├── Button.tsx            # Primary interactive element
├── Badge.tsx             # Status indicators, tags
├── Input.tsx             # Text input field
├── Select.tsx            # Dropdown select
├── Alert.tsx             # Error/warning/info messages
├── LoadingSpinner.tsx    # Loading states
├── PageHeader.tsx        # Page title + description
├── StatCard.tsx          # Numeric stat display
└── EmptyState.tsx        # No data placeholder
```

### Component Specifications

#### 1. Card

**Purpose:** Container for grouped content
**Variants:** default, hover, interactive

```tsx
// Default Card
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>

// Interactive Card (clickable)
<Card variant="interactive" href="/path">
  Content
</Card>
```

**Styling:**
- Background: `bg-white`
- Border: `border border-gray-200`
- Border radius: `rounded-lg`
- Shadow: `shadow-md`
- Padding: `p-6`
- Hover: `hover:shadow-lg hover:border-blue-500` (interactive only)

---

#### 2. Table

**Purpose:** Display tabular data with sorting
**Features:** Sortable columns, hover states, responsive

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead sortable onSort={handleSort}>Name</TableHead>
      <TableHead>IPR</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>John Doe</TableCell>
      <TableCell>4.52</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Styling:**
- Container: `overflow-x-auto`
- Table: `min-w-full divide-y divide-gray-200`
- Header: `bg-gray-50 text-xs font-medium text-gray-500 uppercase`
- Body: `bg-white divide-y divide-gray-200`
- Row hover: `hover:bg-gray-50`
- Cell padding: `px-6 py-4`

---

#### 3. Button

**Purpose:** Interactive actions
**Variants:** primary, secondary, ghost, danger

```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click Me
</Button>
```

**Variants:**
- **Primary:** `bg-blue-600 text-white hover:bg-blue-700`
- **Secondary:** `bg-gray-200 text-gray-900 hover:bg-gray-300`
- **Ghost:** `bg-transparent border border-gray-300 hover:bg-gray-50`
- **Danger:** `bg-red-600 text-white hover:bg-red-700`

**Sizes:**
- **sm:** `px-3 py-1.5 text-sm`
- **md:** `px-4 py-2 text-base`
- **lg:** `px-6 py-3 text-lg`

---

#### 4. Badge

**Purpose:** Status indicators, labels, tags
**Variants:** default, success, warning, error, info

```tsx
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
```

**Styling:**
- Base: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium`
- **Default:** `bg-gray-100 text-gray-800`
- **Success:** `bg-green-100 text-green-800`
- **Warning:** `bg-yellow-100 text-yellow-800`
- **Error:** `bg-red-100 text-red-800`
- **Info:** `bg-blue-100 text-blue-800`

---

#### 5. Alert

**Purpose:** System messages, errors, warnings
**Variants:** error, warning, success, info

```tsx
<Alert variant="error" title="Error">
  Failed to load data. Please try again.
</Alert>
```

**Styling:**
- Base: `px-4 py-3 rounded border`
- **Error:** `bg-red-50 border-red-200 text-red-700`
- **Warning:** `bg-yellow-50 border-yellow-200 text-yellow-700`
- **Success:** `bg-green-50 border-green-200 text-green-700`
- **Info:** `bg-blue-50 border-blue-200 text-blue-700`

---

#### 6. Input

**Purpose:** Text input fields
**Features:** Labels, validation states, help text

```tsx
<Input
  label="Player Name"
  placeholder="Search players..."
  value={value}
  onChange={handleChange}
  error={errorMessage}
/>
```

**Styling:**
- Label: `block text-sm font-medium text-gray-700 mb-1`
- Input: `w-full px-3 py-2 border border-gray-300 rounded-md`
- Focus: `focus:outline-none focus:ring-2 focus:ring-blue-500`
- Error: `border-red-300 focus:ring-red-500`

---

#### 7. PageHeader

**Purpose:** Consistent page titles and descriptions

```tsx
<PageHeader
  title="Players"
  description="Browse and search player statistics"
/>
```

**Styling:**
- Title: `text-3xl font-bold text-gray-900`
- Description: `text-gray-600 mt-2`
- Container: `space-y-2`

---

#### 8. StatCard

**Purpose:** Display numeric statistics

```tsx
<StatCard
  label="Total Matches"
  value={142}
  trend="+12%"
  trendDirection="up"
/>
```

**Styling:**
- Container: Card with `text-center`
- Label: `text-sm font-medium text-gray-600`
- Value: `text-3xl font-bold text-gray-900`
- Trend (up): `text-sm text-green-600`
- Trend (down): `text-sm text-red-600`

---

#### 9. LoadingSpinner

**Purpose:** Loading states

```tsx
<LoadingSpinner size="md" text="Loading players..." />
```

**Variants:**
- Full page: Centered with min-height
- Inline: Small spinner next to text
- Overlay: Semi-transparent backdrop

---

#### 10. EmptyState

**Purpose:** No data placeholders

```tsx
<EmptyState
  icon={<SearchIcon />}
  title="No players found"
  description="Try adjusting your search criteria"
/>
```

**Styling:**
- Container: `text-center py-12`
- Icon: `text-gray-400 mb-4`
- Title: `text-lg font-medium text-gray-900`
- Description: `text-gray-600`

---

## Patterns

### Page Layout Pattern

Every page should follow this structure:

```tsx
export default function PageName() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Page Title"
        description="Page description"
      />

      {/* Filters/Controls (optional) */}
      <Card>
        <form>
          {/* Input fields */}
        </form>
      </Card>

      {/* Error State */}
      {error && <Alert variant="error">{error}</Alert>}

      {/* Empty State */}
      {!loading && data.length === 0 && (
        <EmptyState title="No data" />
      )}

      {/* Main Content */}
      {data.length > 0 && (
        <Card>
          <Table>
            {/* Table content */}
          </Table>
        </Card>
      )}

      {/* Footer Info */}
      <div className="text-center text-sm text-gray-600">
        Showing {data.length} items
      </div>
    </div>
  );
}
```

### List Page Pattern

For pages displaying lists of items (teams, players, machines):

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => (
    <Card key={item.id} variant="interactive" href={`/items/${item.id}`}>
      <CardTitle>{item.name}</CardTitle>
      <CardContent>
        <dl className="space-y-1 text-sm text-gray-600">
          <div><dt className="font-medium">Label:</dt> <dd>Value</dd></div>
        </dl>
      </CardContent>
    </Card>
  ))}
</div>
```

### Detail Page Pattern

For individual item detail pages:

```tsx
<div className="space-y-6">
  <PageHeader title={item.name} description={item.description} />

  {/* Stats Grid */}
  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    <StatCard label="Stat 1" value={value1} />
    <StatCard label="Stat 2" value={value2} />
    <StatCard label="Stat 3" value={value3} />
  </div>

  {/* Detailed Data */}
  <Card>
    <CardHeader><CardTitle>Detailed Information</CardTitle></CardHeader>
    <CardContent>
      <Table>
        {/* Data table */}
      </Table>
    </CardContent>
  </Card>
</div>
```

### Form Pattern

Consistent form layouts:

```tsx
<Card>
  <form onSubmit={handleSubmit} className="space-y-4">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Input label="Field 1" {...field1Props} />
      <Input label="Field 2" {...field2Props} />
    </div>

    <div className="flex justify-end gap-2">
      <Button variant="ghost" type="button">Cancel</Button>
      <Button variant="primary" type="submit">Submit</Button>
    </div>
  </form>
</Card>
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)
- [x] Create design system document
- [ ] Enhance `globals.css` with CSS custom properties for all colors
- [ ] Create `/components/ui/` directory structure
- [ ] Build core components: Card, Button, Badge, Alert

### Phase 2: Data Components (Week 2)
- [ ] Build Table component with sorting
- [ ] Build Input and Select components
- [ ] Build PageHeader component
- [ ] Build LoadingSpinner and EmptyState components

### Phase 3: Migration (Week 3)
- [ ] Refactor Players page to use new components
- [ ] Refactor Teams page to use new components
- [ ] Refactor Machines page to use new components
- [ ] Refactor Venues page to use new components

### Phase 4: Advanced Components (Week 4)
- [ ] Build StatCard component
- [ ] Build Chart wrapper components (if needed)
- [ ] Create specialized components for MNP-specific patterns
- [ ] Documentation updates

### Phase 5: Polish (Week 5)
- [ ] Dark mode refinement
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] User testing and feedback

---

## Development Guidelines

### Component Development

1. **Start with TypeScript interfaces:**
   ```tsx
   interface CardProps {
     children: React.ReactNode;
     variant?: 'default' | 'interactive';
     className?: string;
   }
   ```

2. **Use composition patterns:**
   ```tsx
   Card.Header = CardHeader;
   Card.Content = CardContent;
   Card.Footer = CardFooter;
   ```

3. **Support className override:**
   ```tsx
   className={cn(baseStyles, className)}
   ```

4. **Export from index:**
   ```tsx
   // components/ui/index.ts
   export { Card } from './Card';
   export { Button } from './Button';
   ```

### Testing Checklist

For each component:
- [ ] Renders correctly with default props
- [ ] All variants work as expected
- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Responsive on mobile/tablet/desktop
- [ ] Dark mode looks good
- [ ] Performance is acceptable

### Accessibility Requirements

- **Interactive elements** must have visible focus indicators
- **Links** must be distinguishable from regular text
- **Form inputs** must have associated labels
- **Color** must not be the only way to convey information
- **Contrast ratios** must meet WCAG AA (4.5:1 for text, 3:1 for UI)

---

## Resources

### Design References
- [Tailwind UI Components](https://tailwindui.com/)
- [Shadcn/ui](https://ui.shadcn.com/) - Component patterns
- [Radix UI](https://www.radix-ui.com/) - Accessibility primitives

### Tools
- [Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Aria](https://react-spectrum.adobe.com/react-aria/) - Accessible component hooks

---

**Maintained by:** JJC
**For questions or suggestions:** Update this document via PR
