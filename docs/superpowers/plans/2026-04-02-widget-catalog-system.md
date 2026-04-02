# Widget Catalog System — Implementation Plan

**Date:** 2026-04-02
**Status:** Planned
**Module:** Pessoal (Personal Organizer)

---

## Core Concept

A "+" button opens a widget catalog panel. User picks a widget type, it gets added to the gridstack grid at the next available position. Each widget can be removed via an "x" button on its header (hover-visible). Widgets are fully draggable/resizable. Layout persists per profile in localStorage.

## Widget Categories & Types

### Personal Organizer (existing — already built)

| Widget | Type Key | Default Size | Description |
|---|---|---|---|
| Tasks | `tasks` | 4×6 | Task list with filters, projects, priorities |
| Reminders | `reminders` | 5×6 | Apple Reminders integration |
| Calendar | `calendar` | 3×8 | Month grid with personal events |
| Upcoming Events | `events` | 4×5 | Next 14 days event list |
| Notes | `notes` | 5×5 | Personal notes with pin/edit |
| Quick Capture | `capture` | 8×1 | Task/note creation form |
| Projects Bar | `projects` | 4×1 | Project filter/create |
| KPI: Hoje | `kpi-hoje` | 3×2 | Tasks due today count |
| KPI: Atrasadas | `kpi-atrasadas` | 3×2 | Overdue task count |
| KPI: Ativas | `kpi-ativas` | 3×2 | Active task count |
| KPI: Projetos | `kpi-projetos` | 3×2 | Active project count |

### Text/Display (new)

| Widget | Type Key | Default Size | Description |
|---|---|---|---|
| Text Block | `text-block` | 4×2 | Plain text/markdown card — titles, sections, comments. Editable inline. Stored in PersonalNote with a `widget_type` field or separate model. |
| Clock | `clock` | 2×2 | Current time + date display, updates every minute |
| Greeting | `greeting` | 4×1 | "Bom dia, Palmer" with formatted date |

### Finance — from Financeiro module (new)

These call the existing `/api/analytics/metricas/` endpoint and display single values.

| Widget | Type Key | Default Size | Description |
|---|---|---|---|
| Saldo Projetado | `fin-saldo` | 3×2 | Projected balance for current month (`saldo_projetado`) |
| Sobra do Mes | `fin-sobra` | 3×2 | Budget remaining = orcamento variavel − variable spending |
| Fatura CC | `fin-fatura` | 3×2 | Credit card bill total for current month (`fatura_total`) |
| Gastos Variaveis | `fin-variavel` | 3×2 | Variable spending vs budget (amount + progress bar) |
| Proximos Vencimentos | `fin-vencimentos` | 4×4 | Upcoming fixo payments due this month (list) |

### Integrations (low priority)

| Widget | Type Key | Default Size | Description |
|---|---|---|---|
| Weather | `weather` | 3×2 | Current weather via free API (OpenWeatherMap) |
| Bookmark Links | `bookmarks` | 3×3 | Quick links grid to frequently used URLs |

## Implementation Structure

### 1. Widget Registry

```javascript
const WIDGET_REGISTRY = {
  'tasks':         { label: 'Tarefas', category: 'Pessoal', defaultW: 4, defaultH: 6, minW: 2, minH: 3, component: TaskList },
  'reminders':     { label: 'Lembretes', category: 'Pessoal', defaultW: 5, defaultH: 6, minW: 2, minH: 3, component: PersonalReminders },
  'calendar':      { label: 'Calendario', category: 'Pessoal', defaultW: 3, defaultH: 8, minW: 2, minH: 4, component: PersonalCalendar },
  // ... etc
  'text-block':    { label: 'Texto', category: 'Display', defaultW: 4, defaultH: 2, minW: 2, minH: 1, component: TextBlock },
  'fin-saldo':     { label: 'Saldo Projetado', category: 'Financeiro', defaultW: 3, defaultH: 2, minW: 2, minH: 1, component: FinSaldo },
  // ... etc
}
```

### 2. Widget State (localStorage)

```javascript
// Array of placed widgets
[
  { id: 'tasks-1', type: 'tasks', x: 0, y: 0, w: 4, h: 6 },
  { id: 'text-abc', type: 'text-block', x: 4, y: 0, w: 4, h: 2, config: { content: 'My section title' } },
  { id: 'fin-saldo-1', type: 'fin-saldo', x: 0, y: 6, w: 3, h: 2 },
]
```

Each widget gets a unique `id` (type + random suffix). `config` holds widget-specific data (e.g., text content for text-block, URL list for bookmarks).

### 3. Add Widget Button

Floating "+" button (bottom-right or top-right corner) that opens a categorized dropdown:

```
[+] ──────────────────
  Pessoal
    ☐ Tarefas
    ☐ Lembretes
    ☐ Calendario
    ...
  Display
    ☐ Texto
    ☐ Relogio
    ☐ Saudacao
  Financeiro
    ☐ Saldo Projetado
    ☐ Sobra do Mes
    ☐ Fatura CC
    ...
──────────────────────
```

Clicking a widget type adds it to the grid at the first available position.

### 4. Remove Widget

Each widget header shows an "x" button on hover (right side). Clicking removes it from the grid and state. Existing widgets (tasks, reminders, etc.) that are removed can be re-added from the catalog.

### 5. Finance Widget Implementation

Finance widgets call the existing metricas API:

```javascript
function FinSaldo() {
  const { data } = useQuery({
    queryKey: ['metricas-widget'],
    queryFn: () => api.get(`/analytics/metricas/?month_str=${currentMonthStr}`),
    staleTime: 60000,
  })
  const saldo = data?.saldo_projetado || 0
  return (
    <div className={styles.finCard}>
      <span className={styles.finValue}>R$ {saldo.toLocaleString('pt-BR')}</span>
      <span className={styles.finLabel}>Saldo Projetado</span>
    </div>
  )
}
```

### 6. Text Block Widget

Editable inline text card. Content stored in widget config (localStorage). Double-click to edit, blur to save.

```javascript
function TextBlock({ config, onConfigChange }) {
  const [editing, setEditing] = useState(false)
  const [text, setText] = useState(config?.content || '')
  // ... inline edit with textarea
}
```

## Priority Order

1. **Widget registry + add/remove controls** — the infrastructure
2. **Text Block widget** — immediately useful for section titles/notes
3. **Finance widgets** (Saldo, Sobra, Fatura) — cross-module integration
4. **Greeting + Clock widgets** — polish
5. **Weather/Bookmarks** — low priority, nice-to-have

## Dependencies

- Existing `/api/analytics/metricas/` endpoint for finance widgets
- Existing PersonalTask/Project/Note models for KPI computations
- gridstack.js API: `grid.addWidget()`, `grid.removeWidget()`, `grid.save()`
