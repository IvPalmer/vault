# Calendar Widget: Current Time Indicator — Design Spec
**Date:** 2026-04-08  
**Scope:** `PersonalOrganizer.jsx` + `PersonalOrganizer.module.css` — Option A

## Overview
Add a current-time indicator line to the week and day views of `PersonalCalendar`,
plus upgrade the day view from a flat event list to a proper hour-grid (matching the
week view structure) so the line is meaningful in both views.

## 1. Time Tracking

```js
const [nowTime, setNowTime] = useState(new Date())
useEffect(() => {
  const id = setInterval(() => setNowTime(new Date()), 60000)
  return () => clearInterval(id)
}, [])
```

`nowTime` is used to compute both the indicator position and auto-scroll offset.

## 2. Auto-scroll

A `scrollRef` is attached to `calWeekScroll` (week) and the new `calDayScroll` (day).
On mount and on viewMode change, scroll to `(nowHour - 6) * ROW_HEIGHT - 80` so the
current hour appears with ~2 rows of context above it.

```js
const ROW_HEIGHT = 40 // matches minHeight in CSS
const scrollRef = useRef(null)
useEffect(() => {
  if ((viewMode === 'week' || viewMode === 'day') && scrollRef.current) {
    const h = nowTime.getHours()
    scrollRef.current.scrollTop = Math.max(0, (h - 6) * ROW_HEIGHT - 80)
  }
}, [viewMode])
```

## 3. Time Line — Week View

The time line renders inside `calWeekScroll`, in the row matching `nowTime.getHours()`,
only when today is in the current week.

- `calWeekRow` gets `position: relative` (CSS change)
- Inside the matching row, absolutely-positioned `<div className={styles.nowLine}>`
- Top offset: `(nowTime.getMinutes() / 60) * ROW_HEIGHT`
- Extends from gutter edge (left: 48px) to right: 0
- A small circle `<span className={styles.nowDot}>` at left edge of line

```jsx
{h === nowTime.getHours() && todayInWeek && (
  <div className={styles.nowLine} style={{ top: `${(nowTime.getMinutes() / 60) * ROW_HEIGHT}px` }}>
    <span className={styles.nowDot} />
  </div>
)}
```

## 4. Day View — Rewrite as Time Grid

Replace the flat `calDayView` list with an hour grid identical to the week view,
but with a single data column instead of 7.

Structure:
```
calWeekFixed  ← all-day events (if any)
calDayScroll  ← scrollable hour grid (ref=scrollRef)
  calWeekRow (for each hour 6–23)
    calWeekGutter  ← time label
    calDayCell     ← single column, events for this hour
    [nowLine if today && h === nowHour]
```

Events are placed in their hour slot by `getHours()` of start time, same logic as week.
All-day events move to a fixed header above the scroll.

## 5. CSS Changes

New classes:
- `.nowLine` — `position: absolute; left: 48px; right: 0; height: 2px; background: var(--color-red); pointer-events: none; z-index: 2;`
- `.nowDot` — `position: absolute; left: -4px; top: -3px; width: 8px; height: 8px; border-radius: 50%; background: var(--color-red);`
- `.calDayScroll` — same as `.calWeekScroll` (flex: 1, overflow-y: auto, min-height: 0)
- `.calDayCell` — same as `.calWeekCell` but takes remaining width after gutter

Changed:
- `.calWeekRow` — add `position: relative`

## 6. Files Changed

| File | Change |
|------|--------|
| `src/components/PersonalOrganizer.jsx` | nowTime state, scrollRef, week line, day view rewrite |
| `src/components/PersonalOrganizer.module.css` | nowLine, nowDot, calDayScroll, calDayCell, calWeekRow position |

No new files. No backend changes.
