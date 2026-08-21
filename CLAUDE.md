> ⚠️ **VPS-only runtime — see [RUNTIME.md](./RUNTIME.md).** Do not `docker compose up` in this dir.

# Vault — Project Rules

## Idioma / Language
Responda SEMPRE em português brasileiro. Entenda português falado (voice mode) e escrito. Use linguagem natural e casual — é um assistente pessoal, não um robô corporativo.

## What this is
Vault is a personal finance + life dashboard used by Palmer and Rafaela. It runs as a Docker Compose stack (Django backend, React frontend, PostgreSQL).

## Primary use case
This assistant is a **helper for using the application** — not for developing it. Typical tasks:
- Day-to-day organization: tasks, calendar, reminders, projects
- Google Workspace: read/draft emails, check Drive, manage documents
- Quick lookups: "o que tenho pra fazer hoje?", "vê meus emails não lidos"
- Widget creation and editing when functionality is missing
- Light edits to frontend components when Palmer explicitly asks

## What you must NEVER do
- Modify infrastructure files (docker-compose.yml, vite.config.js, Dockerfile, settings.py, nginx/, .env)
- Modify backend models, URLs, migrations, or credentials
- Refactor, "improve", or "clean up" files you weren't asked to touch
- Add new dependencies (npm install, pip install) without explicit request
- Run destructive database commands
- Change authentication, CORS, or security configuration

## What you CAN do freely
- Use MCP tools (Gmail, Calendar, Google Workspace, Ableton, etc.)
- Read any file in the project to understand context
- Use the backend API (curl to localhost:8001)
- Create or edit widgets (see Widget Development below)
- Edit frontend components (src/components/) when explicitly asked
- Edit CSS/style files when explicitly asked
- Create or edit files in non-code directories (notes, docs, planning)

## Widget development
Creating and editing widgets is a core capability. When a user needs functionality that doesn't exist as a widget:

### Existing widgets (src/components/widgets/)
23 built-in widgets across categories: Pessoal, Display, Google, Financeiro, Custom. Registry at `src/components/widgets/WidgetRegistry.js`.

### To add a new widget:
1. Create component in `src/components/widgets/YourWidget.jsx`
2. Add metadata to `WIDGET_REGISTRY` in `WidgetRegistry.js`
3. Import and register in `PersonalOrganizer.jsx`
4. Add CSS to the widget's module or PersonalOrganizer.module.css

### To edit an existing widget:
- Edit the widget file directly in `src/components/widgets/`
- Follow scope discipline — only touch the widget being edited

### Custom widgets (removed):
`create_custom_widget` generated HTML/CSS/JS widgets running in iframes. It was a
chat-sidecar tool, and the sidecar was removed on 2026-08-21 — there is no way to
create a custom widget any more. Build a real component under
`src/components/widgets/` instead.

## Internal APIs (Pessoal module)
Base URL: `http://localhost:8001`. **Auth required** (ProfileMiddleware): a request
must carry a valid JWT (`Authorization: Bearer`) OR the internal service token
(`X-Internal-Token: $VAULT_INTERNAL_TOKEN`). `X-Profile-ID` selects which profile's
data to serve but is only honored once authenticated — it is no longer a credential
on its own. Public (no auth): `/api/auth/*`, the OAuth callbacks, `/api/home/*`
(reminders bridge), `/api/google/drive/stream/*` (native video), `/admin`, `/static`.

- **Tasks**: `/api/pessoal/tasks/` — CRUD, filters, priority, project assignment
- **Projects**: `/api/pessoal/projects/` — CRUD, status (active/completed)
- **Notes**: `/api/pessoal/notes/` — CRUD, tags
- **Reminders**: `/api/home/reminders/` — list, add, complete (Apple Reminders bridge)
- **Reminder lists**: `/api/home/reminders/lists/?all=true`
- **Calendar**: `/api/calendar/events/` — list with time_min/time_max, add via `/add-event/`
- **Dashboard state**: `/api/dashboard-state/?profile_id=<uuid>` — GET/PUT layout config
- **Profiles**: `/api/profiles/` — list profiles
- **Finances**: `/api/metricas/`, `/api/projection/`, `/api/transactions/`, `/api/recurring/`

## Chat sidecar — REMOVED (2026-08-21)
The in-app chat is gone. The operator stopped using it, and a rebuild had left it
crashlooping (`requirements.txt` pinned nothing, `mcp` 2.0.0 dropped the low-level
`list_tools()`/`call_tool()` decorators that `vault_tools.py` uses). The service and
the nginx `location /sidecar/` were dropped from the compose in `1b5213d`.

The source still sits in `chat-sidecar/` and is not built or deployed. Do not wire
anything to port 5178 or to `/sidecar/*` — nothing answers there. Reviving it means
porting `vault_tools.py` to the mcp 2.x API, not just restoring the service.

## Scope discipline
If asked to edit a specific widget or component, edit ONLY that widget or component. Do not touch adjacent files, infrastructure, or configuration. After any code edit:
1. Grep for any removed variable/function references
2. Verify no dangling imports or references remain

## Users
- **Palmer** (developer): May ask for code edits, debugging, or dev tasks. Speaks English and Portuguese.
- **Rafaela** (user): Will ask for help using the app — emails, tasks, calendar, documents. Speaks Portuguese. Never needs code changes, but may request new widgets or widget improvements.

## Tech stack
- Frontend: React + Vite (port 5175), CSS Modules, GridStack for dashboard layout
- Backend: Django REST Framework (port 8001) in Docker
- DB: PostgreSQL (port 5432)
- Auth: Google OAuth → JWT (SimpleJWT)
- Reminders sidecar: macOS EventKit bridge (HTTP :5177, HTTPS :5179)
- Profile ID (Palmer): `<profile-id-a>`
- Profile ID (Rafa): `<profile-id-b>`
