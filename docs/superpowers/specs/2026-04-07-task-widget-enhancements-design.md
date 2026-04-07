# Task Widget Enhancements — Design Spec
**Date:** 2026-04-07  
**Scope:** `PersonalOrganizer.jsx` only (Option A — surgical)

---

## Overview

Two improvements to the `tasks` widget:

1. **Project filter** — per-widget project selector with real-time toggle in the header and a persistent default in settings
2. **Kanban view** — the existing grid icon becomes a list ↔ kanban toggle; kanban shows 3 columns (A Fazer / Fazendo / Feito)

Both states are persisted via `config`/`onConfigChange` (dashboard state server-side).

---

## 1. Config & Props

`TaskList` currently receives only `activeProject`. It gains:

```jsx
function TaskList({ activeProject, config, onConfigChange })
```

The switch-case that renders the tasks widget becomes:

```jsx
case 'tasks':
  return (
    <TaskList
      activeProject={activeProject}
      config={widgetConfigs[widget.id]}
      onConfigChange={(cfg) => updateWidgetConfig(widget.id, cfg)}
    />
  )
```

Config shape (persisted in dashboard state):
```js
{
  projectFilter: '',   // '' = all, or project ID string
  viewMode: 'list',    // 'list' | 'kanban'
}
```

Local helper inside `TaskList`:
```js
const update = (patch) => onConfigChange?.({ ...config, ...patch })
```

---

## 2. Project Filter

### Header select
A compact `<select>` appears in the widget header, between the title and the right icons:

```
TAREFAS  [Todos ▾]  [kanban icon]  [badge]
```

- Options: `Todos os projetos` (value `''`) + one `<option>` per project
- `value` = `config?.projectFilter ?? ''` (read directly from config — no separate local state needed since `onConfigChange` triggers re-render)
- `onChange` calls `update({ projectFilter: value })` — persists immediately
- Width: `auto`, styled like the existing `captureSelect`

### Filtering logic
Replace the existing `activeProject` filter inside `allTasks` useMemo:

```js
const effectiveProject = (config?.projectFilter || activeProject) || ''

const allTasks = useMemo(() => {
  let list = data?.results || data || []
  if (effectiveProject) list = list.filter((t) => t.project === effectiveProject)
  return list
}, [data, effectiveProject])
```

`activeProject` (global, from ProjectsBar) is used as fallback when no per-widget filter is set.

### Settings panel (gear icon)
A `SettingsGearButton` + `WidgetSettingsPanel` are added to `TaskList`. Settings fields:

| Field | Control | Persists to |
|-------|---------|-------------|
| Projeto padrão | `<select>` (same options as header) | `config.projectFilter` |
| Visualização padrão | `<select>` Lista / Kanban | `config.viewMode` |

---

## 3. Kanban View

### Toggle
The existing grid icon button (currently toggles `groupBy`) becomes the list ↔ kanban toggle:

```js
const viewMode = config?.viewMode ?? 'list'
// toggle:
update({ viewMode: viewMode === 'list' ? 'kanban' : 'list' })
```

Icon stays the same (4 squares). Active state uses the existing `groupToggleActive` class.

### Layout
Three fixed columns side by side, each filling the widget height with independent scroll:

```
┌─────────────┬──────────────┬──────────────┐
│  A FAZER  3 │  FAZENDO  1  │   FEITO   5  │
├─────────────┼──────────────┼──────────────┤
│  [card]     │  [card]      │  [card]      │
│  [card]     │              │  [card]      │
└─────────────┴──────────────┴──────────────┘
```

- Column header: label + count badge
- Each card: title, priority badge (if > 0), due date (if set), project name (if `effectiveProject === ''`)
- Clicking a card opens the existing expanded panel inline below the card, same as in list mode (reuses `expandedId` state + `renderTask` / `expandTask` logic unchanged)
- The filter tabs (Ativas / Fazendo / Feito) are **hidden** in kanban mode — all tasks shown across the 3 columns
- Columns use `flex: 1`, `overflow-y: auto`, `border-right` separator, no drag-and-drop

### New CSS classes needed (in `PersonalOrganizer.module.css`)
- `.kanbanBoard` — `display: flex; flex: 1; overflow: hidden; gap: 0;`
- `.kanbanCol` — `flex: 1; display: flex; flex-direction: column; overflow: hidden; border-right: 1px solid var(--color-border);`
- `.kanbanColHeader` — column title + count, styled like filter tab headers
- `.kanbanColBody` — `flex: 1; overflow-y: auto; padding: 6px;`
- `.kanbanCard` — card per task, `background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 8px; margin-bottom: 6px; cursor: pointer;`
- `.kanbanCardTitle` — task title, `font-size: 0.82rem; font-weight: 500;`
- `.kanbanCardMeta` — priority + due + project, `display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px;`

---

## 4. What Does NOT Change

- `renderTask` / expanded panel — reused as-is in both list and kanban modes
- `cycleMutation`, `updateMutation`, `deleteMutation`, `addMutation` — unchanged
- The inline add-task form at the bottom — remains in list mode; hidden in kanban mode (kanban is read/manage only, add via list or QuickCapture)
- `groupBy` state — removed (its functionality is now replaced by kanban columns)
- All other widgets — untouched

---

## 5. Files Changed

| File | Change |
|------|--------|
| `src/components/PersonalOrganizer.jsx` | TaskList props, project filter, kanban render, settings panel |
| `src/components/PersonalOrganizer.module.css` | New kanban CSS classes |

No new files. No backend changes.

---

## 6. Out of Scope

- Drag-and-drop between kanban columns (future)
- Multiple project filters / multi-select (future)
- Kanban for the reminders widget (future)
