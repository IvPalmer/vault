# Vault — Next Phases Implementation Plan

> Created: February 2026
> Purpose: Detailed roadmap for extending the Family Hub with new modules
> Reference: Based on competitive analysis (Homechart, HomeHub, Honeydue, FamilyWall)

---

## Architecture Overview (Current State)

```
┌──────────────────────────────────────────────────────┐
│  /home  (Family Hub — shared, no profile required)   │
│  ┌─────────────┐ ┌─────────────┐ ┌────────────────┐ │
│  │  Reminders   │ │  Notes      │ │  Calendar      │ │
│  │  (EventKit)  │ │  (Django)   │ │  (Google API)  │ │
│  └─────────────┘ └─────────────┘ └────────────────┘ │
├──────────────────────────────────────────────────────┤
│  /:profileSlug/*  (Profile-scoped modules)           │
│  ┌──────────────────────────────────────────────────┐│
│  │  Financeiro (complete — 40+ endpoints)            ││
│  └──────────────────────────────────────────────────┘│
│  ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────────┐ │
│  │Compras │ │Viagens │ │Documentos│ │  (future)   │ │
│  │  TBD   │ │  TBD   │ │   TBD    │ │             │ │
│  └────────┘ └────────┘ └──────────┘ └─────────────┘ │
└──────────────────────────────────────────────────────┘
```

**Tech stack**: Django 5.2 + DRF | React 18 + Vite + TanStack Query | PostgreSQL 15 | Docker
**Integrations**: Apple Reminders (EventKit sidecar), Google Calendar (OAuth2)
**Access**: LAN via http://raphaels-mac-studio.local:5175/home

---

## Phase 13 — Home Screen Enhancement: "Today View" + Financial Awareness

**Goal**: Make `/home` the single source of truth for "what's happening today" by surfacing financial data alongside existing widgets.

### 13A. Upcoming Bills Widget
Show the next 7 days of financial due dates on the home screen.

**Backend**:
- New endpoint: `GET /api/home/upcoming-bills/?days=7`
- Query `RecurringTemplate` for items with `due_day` falling in the next N days
- Query `RecurringMapping` for current month's actual vs expected amounts
- Return: `[{ name, due_day, expected_amount, status, days_until }]`
- Exempt from profile middleware (show both Palmer + Rafa's bills combined)

**Frontend** (`Home.jsx`):
- New `UpcomingBillsWidget` component between Module Cards and the grid
- Horizontal scrollable card strip showing upcoming bills
- Each card: icon (colored by status), name, amount, "vence em X dias" or "venceu há X dias"
- Color coding: green (paid/mapped), orange (upcoming 1-3 days), red (overdue/missing)
- Click → navigate to `/:profileSlug/overview` at the recurring section

**CSS**: ~60 lines in `Home.module.css`

### 13B. Calendar Aggregation
Surface financial due dates as calendar events alongside Google Calendar events.

**Backend**:
- Extend `GET /api/home/calendar/events/` with optional `?include_bills=true`
- When true, merge RecurringTemplate due dates into the events array
- Bill events use a special `source: 'vault-finance'` flag so frontend can style differently

**Frontend** (`Home.jsx` CalendarWidget):
- Financial due dates show as red/orange dots (vs blue for Google Calendar events)
- Day detail panel groups: "Eventos" section + "Contas" section
- Bills show amount and status

### 13C. PWA Support
Make Vault installable on Rafa's phone without an app store.

**Files**:
- `public/manifest.json` — App name "Vault", icons, theme_color (burnt orange), display: standalone
- `public/vault-icon-192.png`, `public/vault-icon-512.png` — App icons
- `src/sw.js` — Minimal service worker for offline shell caching
- Update `index.html` with `<link rel="manifest">` and meta tags

**Result**: Rafa can "Add to Home Screen" on Safari → opens like a native app

---

## Phase 14 — Shopping List Module ("Compras")

**Goal**: Shared shopping list that both Palmer and Rafa can edit in real-time from their devices.

### Data Model

```python
# backend/api/models.py

class ShoppingStore(models.Model):
    """Store/location for grouping shopping items."""
    name = models.CharField(max_length=100)           # "Mercado", "Farmácia", "Pet Shop"
    icon = models.CharField(max_length=50, blank=True) # emoji or icon key
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class ShoppingItem(models.Model):
    """Individual item on the shopping list."""
    name = models.CharField(max_length=200)
    store = models.ForeignKey(ShoppingStore, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.CharField(max_length=50, blank=True)  # "2kg", "1L", "3 unidades"
    checked = models.BooleanField(default=False)
    checked_by = models.CharField(max_length=50, blank=True)  # "Palmer" or "Rafaella"
    checked_at = models.DateTimeField(null=True, blank=True)
    added_by = models.CharField(max_length=50, default='')
    notes = models.TextField(blank=True)
    is_staple = models.BooleanField(default=False)     # auto-re-add on schedule
    staple_interval_days = models.IntegerField(null=True, blank=True)  # re-add every N days
    category = models.ForeignKey(                       # link to budget category
        'Category', on_delete=models.SET_NULL, null=True, blank=True
    )
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['checked', 'display_order', '-created_at']
```

### API Endpoints

```
GET    /api/home/shopping/                   — List all items (grouped by store)
POST   /api/home/shopping/                   — Add item
PATCH  /api/home/shopping/<id>/              — Update item (check/uncheck, edit)
DELETE /api/home/shopping/<id>/              — Remove item
POST   /api/home/shopping/clear-checked/     — Clear all checked items
GET    /api/home/shopping/stores/            — List stores
POST   /api/home/shopping/stores/            — Add store
GET    /api/home/shopping/suggestions/       — Frequent items for quick-add
```

### Frontend

**New file**: `src/components/Shopping.jsx` (~400 lines)
- Full-page view accessible from Module Card on `/home` or direct at `/compras`
- Store tabs across top (Mercado | Farmácia | Todos)
- Each item: checkbox, name, quantity, store badge, added_by
- Quick-add bar at top with autocomplete from purchase history
- Swipe-to-delete on mobile (touch events)
- "Limpar concluídos" button to clear checked items
- Real-time feel: optimistic updates with TanStack Query mutation

**New file**: `src/components/Shopping.module.css` (~300 lines)

**Home.jsx changes**:
- Activate "Compras" module card → link to `/compras`
- Add mini shopping widget showing unchecked item count: "6 itens pendentes"

### Cross-Module Links
- `ShoppingItem.category` FK → links purchases to budget categories
- Future: when item is checked, optionally log a Transaction in Financeiro

---

## Phase 15 — Document Vault ("Documentos")

**Goal**: Secure storage for important household documents with expiry tracking.

### Data Model

```python
class DocumentFolder(models.Model):
    """Folder for organizing documents."""
    name = models.CharField(max_length=100)     # "Pessoal", "Casa", "Saúde", "Veículos"
    icon = models.CharField(max_length=50, blank=True)
    display_order = models.IntegerField(default=0)

class Document(models.Model):
    """A stored document or credential."""
    folder = models.ForeignKey(DocumentFolder, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)          # "Passaporte Palmer"
    document_type = models.CharField(max_length=50)    # "passport", "insurance", "warranty", "contract", "credential"
    owner = models.CharField(max_length=100, blank=True)  # "Palmer", "Rafaella", "Ambos"

    # Key fields (flexible key-value for different doc types)
    number = models.CharField(max_length=200, blank=True)       # Document number
    issuer = models.CharField(max_length=200, blank=True)       # Issuing entity
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)       # For expiry alerts
    notes = models.TextField(blank=True)
    extra_fields = models.JSONField(default=dict, blank=True)   # Flexible key-value pairs

    # File attachment (optional)
    file = models.FileField(upload_to='documents/', blank=True)
    file_name = models.CharField(max_length=200, blank=True)

    # Alerts
    alert_days_before = models.IntegerField(default=30)  # Alert N days before expiry

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['folder', 'title']
```

### API Endpoints

```
GET    /api/home/documents/                  — List all (grouped by folder)
POST   /api/home/documents/                  — Add document
PATCH  /api/home/documents/<id>/             — Update
DELETE /api/home/documents/<id>/             — Delete
GET    /api/home/documents/folders/          — List folders
POST   /api/home/documents/folders/          — Create folder
GET    /api/home/documents/expiring/         — Documents expiring in next 60 days
POST   /api/home/documents/<id>/upload/      — Upload file attachment
```

### Frontend

**New file**: `src/components/Documents.jsx` (~500 lines)
- Grid view of folders (card-based, like macOS Finder)
- Click folder → list of documents inside
- Document detail: key info displayed as labeled rows
- Expiry badges: green (>60d), yellow (30-60d), red (<30d), grey (no expiry)
- Add document form with type-specific field templates:
  - Passport: number, issue_date, expiry_date, issuer
  - Insurance: policy_number, provider, coverage_amount, expiry_date
  - Warranty: product, purchase_date, expiry_date, store
  - Credential: username, notes (no passwords — refer to 1Password)

**Home.jsx integration**:
- Activate "Documentos" module card
- Show expiring document alert on home: "Passaporte vence em 45 dias"

### Default Folders (seed data)
- Pessoal (CPF, RG, Passaportes, CNH)
- Casa (Contrato aluguel, condomínio, IPTU)
- Saúde (Plano de saúde, exames, receitas)
- Veículos (CRLV, seguro, IPVA)
- Financeiro (Contratos, apólices)

---

## Phase 16 — Notes Upgrade

**Goal**: Transform the flat bulletin board into a structured markdown wiki.

### Model Changes

```python
class FamilyNote(models.Model):
    # Existing fields stay...
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField(blank=True)
    author_name = models.CharField(max_length=100)
    pinned = models.BooleanField(default=False)

    # New fields:
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children')
    tags = models.JSONField(default=list, blank=True)       # ["casa", "urgente"]
    is_markdown = models.BooleanField(default=True)
    color = models.CharField(max_length=20, blank=True)     # Note card color
```

### Frontend Changes
- Render markdown content (add `react-markdown` dependency, ~50KB)
- Hierarchical navigation: breadcrumbs showing parent → child path
- Tag filtering: click a tag to filter notes
- Color-coded note cards (like Google Keep)
- Version history: store edits in a `NoteRevision` model (future)

---

## Phase 17 — Task & Projects Module ("Projetos")

**Goal**: Shared task management beyond Apple Reminders — for household projects with subtasks and deadlines.

### Data Model

```python
class Project(models.Model):
    """A household project or goal."""
    name = models.CharField(max_length=200)        # "Mudança", "Viagem Europa", "Reforma Banheiro"
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='#D2691E')
    status = models.CharField(max_length=20, default='active',
                              choices=[('active','Ativo'), ('paused','Pausado'), ('done','Concluído')])
    due_date = models.DateField(null=True, blank=True)
    budget_estimate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    """A task within a project (or standalone)."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='subtasks')
    title = models.CharField(max_length=300)
    notes = models.TextField(blank=True)
    assigned_to = models.CharField(max_length=100, blank=True)  # "Palmer", "Rafaella", "Ambos"
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurring_interval_days = models.IntegerField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'display_order', 'due_date']
```

### Frontend
- Project board view: columns or list grouped by project
- Task detail: subtasks, assigned person, due date, notes
- Recurring tasks: "Limpar filtro AC" every 90 days
- Calendar integration: task due dates show on `/home` calendar
- Template tasks: reusable checklists (e.g., "Lista de viagem")

---

## Phase 18 — Weather Widget + Daily Briefing

**Goal**: Small quality-of-life additions to the home screen.

### Weather Widget
- Backend: Proxy Open-Meteo API (free, no key) through Django
- Endpoint: `GET /api/home/weather/` — returns current temp, condition, 3-day forecast
- Cache: 15-minute Django cache (avoid rate limits)
- Frontend: Small widget in the greeting area showing temp + icon
- Location: hardcoded to user's city (São Paulo or wherever)

### Morning Briefing (Future)
- Synthesize: calendar events + bills due + tasks due + weather → Portuguese summary
- Display as a dismissible card on `/home` first thing in the morning
- Optional: use Claude API for natural language summary

---

## Implementation Priority & Effort

| Phase | Name | Effort | Impact | Priority |
|-------|------|--------|--------|----------|
| 13A | Upcoming Bills Widget | 2-3 hrs | 🔴 HIGH | Do first |
| 13C | PWA Support | 1-2 hrs | 🔴 HIGH | Do first |
| 14 | Shopping List | 4-6 hrs | 🔴 HIGH | Do second |
| 13B | Calendar Aggregation | 2-3 hrs | 🟡 MEDIUM | With Phase 14 |
| 15 | Document Vault | 4-6 hrs | 🟡 MEDIUM | After shopping |
| 16 | Notes Upgrade | 2-3 hrs | 🟡 MEDIUM | Low effort, nice UX |
| 17 | Tasks & Projects | 6-8 hrs | 🟡 MEDIUM | After docs |
| 18 | Weather + Briefing | 1-2 hrs | 🟢 NICE | Anytime |

**Recommended order**: 13A → 13C → 14 → 13B → 15 → 16 → 17 → 18

---

## Cross-Module Integration Map

```
Shopping ──── budget_category ────→ Financeiro (spending tracking)
Documents ─── expiry_date ────────→ Home Calendar (expiry alerts)
Tasks ──────── due_date ──────────→ Home Calendar (task deadlines)
Bills ──────── due_day ───────────→ Home Calendar (financial events)
                                  → Home Upcoming Bills widget
Shopping ──── suggestions ────────→ Transaction history (frequent merchants)
Projects ──── budget_estimate ────→ Financeiro (project budgeting)
```

---

## File Structure (After All Phases)

```
src/components/
├── Home.jsx                    # Hub: greeting, modules, widgets
├── Shopping.jsx                # Phase 14: Shopping list
├── Shopping.module.css
├── Documents.jsx               # Phase 15: Document vault
├── Documents.module.css
├── Projects.jsx                # Phase 17: Tasks & projects
├── Projects.module.css
├── Layout.jsx                  # Nav: Home | Financeiro | Compras | Docs | Config
├── ...existing finance components...

backend/api/
├── models.py                   # +ShoppingStore, ShoppingItem, DocumentFolder, Document, Project, Task
├── serializers.py              # +new serializers
├── views.py                    # +new view classes
├── urls.py                     # +new route groups
├── google_calendar.py          # Existing
├── services.py                 # Existing finance logic
├── migrations/
│   ├── 0019_shopping.py
│   ├── 0020_documents.py
│   ├── 0021_notes_upgrade.py
│   └── 0022_projects_tasks.py
```

---

## Session Start Checklist

When starting a new session to implement any phase:

1. **Read this file** to understand the plan
2. **Check Docker is running**: `docker ps` (vault-backend-1, vault-db-1)
3. **Check sidecar is running**: `curl http://127.0.0.1:5176/api/home/reminders/lists/`
4. **Check Vite is running**: browser at `http://localhost:5175/home`
5. **Check calendar auth**: `curl http://127.0.0.1:8001/api/home/calendar/status/`
6. **Start implementing** the next phase in order

---

*This plan is a living document. Update after each phase completion.*
