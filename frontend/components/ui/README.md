# UI Component Library - Quick Reference

## Import

```tsx
import { Card, Button, Badge, Alert, Input, Select, Table, PageHeader, LoadingSpinner, EmptyState, StatCard } from '@/components/ui';
```

---

## Components

### Card
```tsx
// Simple card
<Card>
  <Card.Content>Content here</Card.Content>
</Card>

// With header
<Card>
  <Card.Header>
    <Card.Title>Title</Card.Title>
  </Card.Header>
  <Card.Content>Content</Card.Content>
</Card>

// Interactive (clickable)
<Card variant="interactive" href="/path">
  <Card.Content>Content</Card.Content>
</Card>
```

### Button
```tsx
<Button variant="primary" size="md" onClick={handleClick}>
  Click Me
</Button>

// Variants: primary | secondary | ghost | danger
// Sizes: sm | md | lg
```

### Badge
```tsx
<Badge variant="success">Active</Badge>

// Variants: default | success | warning | error | info
```

### Alert
```tsx
<Alert variant="error" title="Error">
  Something went wrong!
</Alert>

// Variants: error | warning | success | info
```

### Input
```tsx
<Input
  label="Player Name"
  type="text"
  placeholder="Search..."
  value={value}
  onChange={handleChange}
  error={errorMessage}
  helpText="Optional help text"
/>
```

### Select
```tsx
<Select
  label="Season"
  value={season}
  onChange={handleChange}
  options={[
    { value: '22', label: 'Season 22' },
    { value: '21', label: 'Season 21' },
  ]}
/>
```

### Table
```tsx
<Table>
  <Table.Header>
    <Table.Row hoverable={false}>
      <Table.Head>Name</Table.Head>
      <Table.Head sortable onSort={handleSort}>Score</Table.Head>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {data.map(item => (
      <Table.Row key={item.id}>
        <Table.Cell>{item.name}</Table.Cell>
        <Table.Cell>{item.score}</Table.Cell>
      </Table.Row>
    ))}
  </Table.Body>
</Table>
```

### PageHeader
```tsx
<PageHeader
  title="Page Title"
  description="Optional description"
  action={<Button>Action</Button>}
/>
```

### LoadingSpinner
```tsx
// Full page
<LoadingSpinner fullPage text="Loading..." />

// Inline
<LoadingSpinner size="sm" text="Loading..." />

// Sizes: sm | md | lg
```

### EmptyState
```tsx
<EmptyState
  icon={<SearchIcon />}
  title="No results"
  description="Try adjusting your filters"
  action={<Button>Clear Filters</Button>}
/>
```

### StatCard
```tsx
<StatCard
  label="Total Games"
  value={142}
  trend="+12%"
  trendDirection="up"
/>

// trendDirection: up | down | neutral
```

---

## Common Patterns

### Page Layout
```tsx
<div className="space-y-6">
  <PageHeader title="Title" description="Description" />

  <Card>
    {/* Filters/Search */}
  </Card>

  {error && <Alert variant="error">{error}</Alert>}

  <Card>
    {/* Main content */}
  </Card>
</div>
```

### Grid of Cards
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => (
    <Card key={item.id} variant="interactive" href={`/items/${item.id}`}>
      <Card.Content>
        {/* Content */}
      </Card.Content>
    </Card>
  ))}
</div>
```

### Form
```tsx
<Card>
  <Card.Content>
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Name" {...props} />
      <Select label="Type" {...props} />

      <div className="flex justify-end gap-2">
        <Button variant="ghost">Cancel</Button>
        <Button variant="primary" type="submit">Submit</Button>
      </div>
    </form>
  </Card.Content>
</Card>
```

### Stat Grid
```tsx
<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
  <StatCard label="Wins" value={42} trend="+5%" trendDirection="up" />
  <StatCard label="Losses" value={18} trend="-3%" trendDirection="down" />
  <StatCard label="Win Rate" value="70%" />
</div>
```

---

## Styling

All components accept a `className` prop for custom styling:

```tsx
<Card className="border-2 border-blue-500">
  <Card.Content className="bg-blue-50">
    Custom styling
  </Card.Content>
</Card>
```

---

## Accessibility

All components include:
- Proper ARIA attributes
- Keyboard navigation support
- Focus indicators
- Semantic HTML
- Screen reader labels

---

## TypeScript

All components are fully typed. Hover over props in your IDE to see available options.

```tsx
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
}
```

---

See [DESIGN_SYSTEM.md](../../DESIGN_SYSTEM.md) for full documentation.
