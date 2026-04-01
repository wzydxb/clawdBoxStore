# React DevTools Profiler Guide

Complete guide to identifying and fixing performance issues using React DevTools Profiler.

## Installation

```bash
# Chrome Extension
https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi

# Firefox Add-on
https://addons.mozilla.org/en-US/firefox/addon/react-devtools/

# Standalone
npm install -g react-devtools
```

---

## The Profiler Tab

### Where to Find It

1. Open React DevTools (browser extension or standalone)
2. Click the **Profiler** tab
3. You'll see:
   - ⏺️ Record button - Start/stop profiling
   - 🔄 Reload and profile button - Profile page load
   - ⚙️ Settings gear - Configure profiling options

---

## Recording a Profile

### Method 1: User Interaction

```
1. Click ⏺️ Record
2. Interact with your app (click button, type, scroll, etc.)
3. Click ⏹️ Stop
4. Analyze the flame graph
```

### Method 2: Page Load

```
1. Click 🔄 Reload and profile
2. Wait for page to fully load
3. Profiler automatically stops
4. Analyze initial render performance
```

---

## Reading the Flame Graph

### What Each Color Means

**Colors** (gradient from green to yellow to red):
- 🟢 **Green**: Fast render (&lt;1ms)
- 🟡 **Yellow**: Moderate render (1-10ms)
- 🔴 **Red**: Slow render (&gt;10ms)

**Width**: How long the component took to render

**Hover**: See exact render time and why it rendered

### Example Interpretation

```
App (25ms)
├── Navbar (2ms)         ✅ Fast
├── Sidebar (1ms)        ✅ Fast
└── Dashboard (22ms)     🔴 SLOW - investigate!
    ├── UserList (20ms)  🔴 SLOW - root cause
    └── Stats (2ms)      ✅ Fast
```

**Diagnosis**: UserList is the bottleneck (20ms of 25ms total)

---

## Understanding "Why Did This Render?"

Click on a component in the flame graph to see:

### 1. Props Changed

```
Why did this render?
• Props changed: { userId: 123 }
```

**Fix**: If props didn't actually change, wrap parent in `React.memo` or memoize the prop value.

### 2. Parent Rendered

```
Why did this render?
• Parent component rendered
```

**Fix**: Wrap this component in `React.memo` to prevent cascading re-renders.

### 3. State Changed

```
Why did this render?
• Hook 1 changed
```

**Fix**: This is expected. Ensure state updates are necessary.

### 4. Context Changed

```
Why did this render?
• Context changed
```

**Fix**: Split context into smaller pieces or memoize context value.

---

## Common Patterns and Fixes

### Pattern 1: Entire Tree Re-renders on Unrelated State Change

**Symptom**: Changing state in Header causes Footer to re-render

**Flame Graph**:
```
App (50ms)              🔴
├── Header (2ms)        🟡
├── Content (40ms)      🔴 Unnecessary
└── Footer (8ms)        🔴 Unnecessary
```

**Fix**: Wrap components in React.memo

```typescript
const Header = React.memo(({ title }) => {
  return <header>{title}</header>;
});

const Content = React.memo(({ children }) => {
  return <main>{children}</main>;
});

const Footer = React.memo(() => {
  return <footer>Footer</footer>;
});
```

**Result**: Only Header re-renders

```
App (2ms)               🟢
└── Header (2ms)        🟢
```

---

### Pattern 2: List Renders Slowly

**Symptom**: Rendering 1000-item list takes &gt;500ms

**Flame Graph**:
```
UserList (500ms)        🔴
├── UserCard (0.5ms) x1000
```

**Fix**: Virtualize with react-window

```typescript
import { FixedSizeList } from 'react-window';

function UserList({ users }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={users.length}
      itemSize={50}
      width="100%"
    >
      {({ index, style }) => (
        <div style={style}>
          <UserCard user={users[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

**Result**: Render time drops to &lt;50ms

```
UserList (50ms)         🟢
└── UserCard (0.5ms) x12  (only visible items)
```

---

### Pattern 3: Parent Passes New Callback on Every Render

**Symptom**: Child wrapped in React.memo still re-renders

**Flame Graph**:
```
Parent (30ms)
└── Child (28ms)        🔴 Re-renders despite React.memo
```

**Why**: Parent passes new function reference

```typescript
// ❌ Creates new function every render
function Parent() {
  return <Child onClick={() => console.log('clicked')} />;
}
```

**Fix**: Memoize callback with useCallback

```typescript
// ✅ Stable function reference
function Parent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <Child onClick={handleClick} />;
}

const Child = React.memo(({ onClick }) => {
  return <button onClick={onClick}>Click me</button>;
});
```

**Result**: Child no longer re-renders

---

### Pattern 4: Expensive Calculation on Every Render

**Symptom**: Component takes 100ms but doesn't render anything complex

**Flame Graph**:
```
ProductList (100ms)     🔴
└── (no children, just slow)
```

**Code**:
```typescript
function ProductList({ products }) {
  // ❌ Sorts on every render
  const sorted = products.sort((a, b) => b.price - a.price);

  return <div>{sorted.map(p => <Product product={p} />)}</div>;
}
```

**Fix**: Memoize expensive calculation

```typescript
function ProductList({ products }) {
  // ✅ Only re-sorts when products change
  const sorted = useMemo(
    () => [...products].sort((a, b) => b.price - a.price),
    [products]
  );

  return <div>{sorted.map(p => <Product product={p} />)}</div>;
}
```

**Result**: Render time drops from 100ms → 5ms

---

## Profiler Settings

### Record Why Components Rendered

**Enable**: Settings ⚙️ → "Record why each component rendered while profiling"

**Benefit**: See exact cause (props, state, context, parent)

**Trade-off**: Slight performance overhead during profiling

### Highlight Updates

**Enable**: Settings ⚙️ → "Highlight updates when components render"

**Benefit**: See which components re-render in real-time (blue flash)

**Use case**: Quickly spot unnecessary re-renders without profiling

---

## Profiling Production Builds

### Why Profile Production?

- Development mode is 2-5x slower (extra checks, warnings)
- Only production profiling shows real user experience
- Tree-shaking and minification affect bundle size

### How to Profile Production

**Option 1: Build with profiling enabled**

```bash
# React (webpack)
npx react-app-rewired build --profile

# Next.js
NEXT_PUBLIC_PROFILING=true npm run build
```

**Option 2: Use profiling build**

```javascript
// Use production build with profiling
import { unstable_trace as trace } from 'scheduler/tracing';
```

---

## Metrics to Target

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| Component render time | &lt;5ms | 5-16ms | &gt;16ms (visible lag) |
| Total page load | &lt;1s | 1-3s | &gt;3s |
| Interaction response | &lt;100ms | 100-300ms | &gt;300ms (feels slow) |
| List item render | &lt;1ms | 1-5ms | &gt;5ms (virtualize) |

**The 16ms Rule**: 60 FPS = 16.67ms per frame. Renders &gt;16ms cause dropped frames.

---

## Real-World Example

### Problem: Slow Dashboard

**Flame Graph**:
```
Dashboard (180ms)       🔴
├── Sidebar (2ms)
├── Header (3ms)
└── DataTable (175ms)   🔴
    ├── TableHeader (2ms)
    └── TableBody (173ms) 🔴
        ├── Row (0.17ms) x1000
```

**Diagnosis**:
1. DataTable is bottleneck (175ms of 180ms)
2. Rendering 1000 rows (0.17ms each = 170ms total)
3. Even though each row is fast, rendering 1000 is slow

**Fix**:
```typescript
import { FixedSizeList } from 'react-window';

function DataTable({ rows }) {
  return (
    <FixedSizeList
      height={600}
      itemCount={rows.length}
      itemSize={40}
    >
      {({ index, style }) => (
        <Row style={style} data={rows[index]} />
      )}
    </FixedSizeList>
  );
}
```

**Result**:
```
Dashboard (15ms)        🟢
├── Sidebar (2ms)
├── Header (3ms)
└── DataTable (10ms)    🟢
    └── Row (0.17ms) x15  (only visible rows)
```

**Improvement**: 180ms → 15ms (92% faster!)

---

## Debugging Workflow

1. **Identify slow component**
   - Record profile
   - Look for red/yellow bars in flame graph
   - Click to see render time

2. **Understand why it's slow**
   - Check "Why did this render?"
   - Is it rendering unnecessarily?
   - Is the render itself expensive?

3. **Apply fix**
   - Unnecessary re-renders? → React.memo, useCallback
   - Expensive calculation? → useMemo
   - Large list? → Virtualization
   - Heavy component? → Code splitting with React.lazy

4. **Verify improvement**
   - Record new profile
   - Compare before/after
   - Target: Green bars, &lt;16ms render time

---

## Common Mistakes

### Mistake 1: Profiling in Development

**Problem**: Dev mode is 2-5x slower than production

**Solution**: Always profile production builds for accurate measurements

### Mistake 2: Optimizing Green Components

**Problem**: Spending time memoizing fast components (&lt;5ms)

**Solution**: Focus on red/yellow bars first (&gt;10ms)

### Mistake 3: Ignoring "Why Did This Render?"

**Problem**: Blindly adding useMemo/useCallback everywhere

**Solution**: Click component to see actual render cause, then fix root issue

### Mistake 4: Not Testing After Changes

**Problem**: Optimization doesn't actually improve performance

**Solution**: Record before/after profiles to verify improvement

---

## Advanced Techniques

### Custom Profiler API

Programmatically measure render performance:

```typescript
import { Profiler } from 'react';

function onRenderCallback(
  id,                  // "DataTable"
  phase,               // "mount" or "update"
  actualDuration,      // Time spent rendering
  baseDuration,        // Estimated time without memoization
  startTime,           // When render started
  commitTime,          // When render committed
  interactions         // Set of interactions
) {
  console.log(`${id} took ${actualDuration}ms to render`);

  // Send to analytics
  if (actualDuration > 16) {
    analytics.track('Slow Render', { id, actualDuration });
  }
}

function App() {
  return (
    <Profiler id="DataTable" onRender={onRenderCallback}>
      <DataTable />
    </Profiler>
  );
}
```

### User Timing API

Add custom markers:

```typescript
function DataTable() {
  performance.mark('data-table-render-start');

  // Rendering logic

  performance.mark('data-table-render-end');
  performance.measure(
    'DataTable Render',
    'data-table-render-start',
    'data-table-render-end'
  );

  return <div>...</div>;
}
```

View in Performance tab of browser DevTools.

---

## Resources

- [React DevTools Profiler Docs](https://react.dev/learn/react-developer-tools)
- [Profiling Performance](https://react.dev/reference/react/Profiler)
- [Chrome Performance Tab](https://developer.chrome.com/docs/devtools/performance/)
