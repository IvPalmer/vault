# Phase 1 Context: UI Foundation

**Phase Goal:** Dashboard has modern, consistent UI with standardized components and inline interactions
**Requirements:** UIUX-01, UIUX-02, UIUX-03, UIUX-04

## Table Component Behavior

**Sorting:**
- All columns sortable by clicking headers
- Toggle ascending/descending on repeated clicks

**Filtering:**
- Global search box above table (filters all visible rows)
- Per-column filter icons for targeted filtering
- Both options available simultaneously

**Selection:**
- Multi-select with checkbox column
- Checkboxes allow selecting multiple rows for bulk actions

**Columns:**
- Fixed widths (no user resizing)
- Column picker to toggle visibility of columns

**Pagination:**
- Infinite scroll within a container
- Each month view only displays transactions for that month
- No traditional page numbers

**Cell Editing:**
- Edit button opens row editing mode
- Original transaction name is read-only (cannot be edited)
- Not cell-by-cell inline editing

**Empty States:**
- Action prompt: "No data yet — import transactions to get started"
- Clear call-to-action when no data exists

**Hover:**
- Subtle row highlight on hover
- Clean visual feedback without being distracting

**Row Actions:**
- Three-dot action menu per row
- Menu contains: edit, delete, duplicate, etc.

**Export:**
- Export button for current view
- CSV format for downloaded data

**Amount Display:**
- Color-coded: green for income, red for expenses
- Sign prefix: +/- shown alongside color
- Both indicators for maximum clarity

## Inline Interaction Mechanics

**Trigger:**
- Click anywhere in the cell to open dropdown
- No need to click specific icon

**Search:**
- Always present in dropdowns
- Type to filter options immediately

**Dismiss:**
- Click outside the dropdown
- Or press Escape key
- Both methods work

**Keyboard Navigation:**
- Full support: arrow keys to navigate
- Enter to select highlighted option
- Escape to close without selecting
- Tab to move to next field

**Grouping:**
- Options grouped under section headers
- Example: categories grouped by type

**Suggestions:**
- Smart/ML-based suggestions at top
- Based on context (what user typically selects)

**Selection Behavior:**
- Immediate save on selection
- No confirmation dialog needed
- Value persists instantly

**Clear Option:**
- Always available (X button or "None" option)
- Works for all dropdown fields, not just optional ones

## Tab Content & Navigation

**Tab Structure:**
Three main tabs positioned horizontally at top (below header):
1. Monthly Overview
2. Analytics
3. Settings

**Monthly Overview Tab:**
Full dashboard containing:
- Transaction table
- Summary metrics cards (income, expenses, balance)
- Recurrents section
- Mini-charts
- Month picker (only place month selection appears)

**Analytics Tab:**
Combined view:
- Charts and trends (spending patterns, category breakdowns)
- Historical comparisons
- Pre-built detailed reports (monthly summary, category drill-down)
- Shows all-time data (not month-scoped)

**Settings Tab:**
All configuration in one place:
- Categories management
- Rules configuration
- Budget settings
- Recurrents setup
- Import settings
- Uses nested tabs for sub-navigation within Settings

**Month Scope:**
- Month picker only appears in Monthly Overview tab
- Analytics shows all-time/historical data by default
- Settings is not month-scoped

**Persistence:**
- Always start at Monthly Overview on fresh session
- No tab state remembered across sessions

**Indicators:**
- No badges, counts, or alert dots on tabs
- Clean, minimal tab appearance

**Sub-Navigation:**
- Nested tabs (secondary tab row) within main tab content
- Used in Settings for Categories, Rules, Budgets, etc.

## Decisions Summary

| Area | Decision |
|------|----------|
| Table sorting | All columns, click to toggle asc/desc |
| Table filtering | Global search + per-column filters |
| Row selection | Multi-select with checkboxes |
| Column resize | Fixed widths, no resize |
| Pagination | Infinite scroll, month-scoped |
| Cell editing | Edit button opens row editing, name read-only |
| Empty state | Action prompt with import CTA |
| Row hover | Subtle highlight |
| Row actions | Three-dot menu |
| Export | CSV export button |
| Amounts | Color + sign prefix |
| Dropdown trigger | Click cell |
| Dropdown search | Always present |
| Dropdown dismiss | Click outside or Escape |
| Dropdown keyboard | Full navigation support |
| Dropdown grouping | Section headers |
| Dropdown suggestions | Smart/ML-based |
| Dropdown save | Immediate |
| Dropdown clear | Always available |
| Tab position | Top horizontal |
| Tab persistence | Always start at Overview |
| Tab indicators | None (clean) |
| Sub-navigation | Nested tabs |
| Overview content | Full dashboard |
| Analytics content | Charts + reports, all-time |
| Settings content | All configuration |
| Month picker | Overview tab only |

---
*Context captured: 2026-01-22*
*Areas discussed: Table Component Behavior, Inline Interaction Mechanics, Tab Content & Navigation*
