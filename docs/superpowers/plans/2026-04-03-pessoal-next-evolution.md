# Pessoal Module — Next Evolution Plan

**Date:** 2026-04-03
**Status:** Discussion / Planning
**Module:** Pessoal (Personal Organizer)

---

## Vision

Pessoal becomes a **single daily hub** — the one place Palmer and Rafa open each morning to see everything: tasks, reminders, calendar, notes, emails, and finances. Widgets are configurable per-user. And at the center: an embedded AI assistant (Claude) with full context of the application, available via chat.

---

## 1. Embedded Claude Chat Assistant

### Concept

A floating chat bubble (bottom-right, next to the "+" catalog button) that opens a conversation with Claude. Each profile gets their own conversation thread. Claude has full context: today's tasks, upcoming events, pending reminders, recent notes, financial summary.

### How It Works

- **Frontend**: Chat widget (floating bubble -> expandable panel) with message history stored in localStorage or DB per profile
- **Backend**: New endpoint `POST /api/pessoal/chat/` that:
  1. Gathers user context (tasks, events, reminders, notes, metricas)
  2. Builds a system prompt with that context
  3. Calls the Anthropic API (`claude-sonnet-4-6` for speed/cost balance)
  4. Streams the response back
- **Auth**: Uses your Anthropic API key (stored in `.env` like Pluggy credentials)
- **Cost**: Normal API pricing. Sonnet is ~$3/M input, $15/M output. A typical daily conversation with context would be ~5-10K tokens input, ~1-2K output per exchange — pennies per conversation
- **Per-profile**: Each profile gets independent chat history and context

### What Claude Knows (System Context)

Each message sends a system prompt like:

```
You are a personal assistant for {profile_name} inside Vault.
Today is {date}. Here is their current state:

TASKS DUE TODAY: {tasks}
OVERDUE TASKS: {overdue}
UPCOMING EVENTS (next 3 days): {events}
PENDING REMINDERS: {reminders}
RECENT NOTES: {notes}
FINANCIAL SUMMARY: saldo R${saldo}, sobra R${sobra}, fatura R${fatura}

Help them with their day. You can suggest task prioritization, help draft documents,
answer questions about their schedule, or help plan their week.
Respond in Portuguese unless they write in English.
```

### Capabilities

- "O que tenho pra fazer hoje?" — summarizes tasks, events, reminders
- "Me ajuda a escrever um email sobre X" — drafts content
- "Qual meu saldo projetado esse mes?" — answers from financial context
- "Adiciona uma tarefa: ligar pro dentista amanha" — could trigger task creation via tool use
- "Resuma minha semana" — weekly planning assistant

### Tool Use (Phase 2)

Claude could have tools to actually modify data:
- `create_task(title, due_date, priority)`
- `create_note(title, content)`
- `complete_task(id)`
- These map to existing API endpoints

### Technical Architecture

**Uses your Claude Max subscription — zero extra cost.** Same approach as your Telegram bot (`claude-assistant`).

- **Backend**: Python sidecar (like reminders-helper) using `claude_agent_sdk` (Claude Agent SDK)
  - Spawns a Claude Code session per profile with a system prompt containing Vault context
  - Exposes `POST /chat` endpoint (SSE streaming)
  - Runs alongside the Django backend, talks to Claude Code CLI locally
  - Uses your Max subscription auth — no API key needed
- **Frontend**: Chat widget with message bubbles, auto-scroll, markdown rendering
- **Context**: System prompt built from Vault's existing API endpoints (tasks, events, metricas)
- **Message history**: SQLite (like claude-assistant) or localStorage

---

## 2. Email Integration (Gmail Widget)

### Concept

Since Google OAuth is already connected (calendar), extend it to read Gmail. New widget types show email notifications and allow basic actions.

### Widget Types

| Widget | Type Key | Description |
|---|---|---|
| Inbox Summary | `email-inbox` | Unread count + latest 5 emails (sender, subject, snippet) |
| Important/Starred | `email-starred` | Starred emails list |
| Email Notifications | `email-notifications` | Badge-style unread count (minimal, like a KPI card) |

### Implementation

- **Backend**: Add Gmail read scope to existing Google OAuth flow
- **Endpoint**: `GET /api/pessoal/emails/?profile_id=X&filter=unread|starred&limit=10`
- **Scopes needed**: `gmail.readonly` (read-only, no sending)
- **Per-profile**: Each profile connects their own Google account (already built for calendar)
- **Refresh**: Poll every 2-5 minutes, or use Gmail push notifications

### Phase 2

- Reply/compose from within Vault (needs `gmail.send` scope)
- Email search widget
- Integration with Claude chat ("summarize my unread emails")

---

## 3. Configurable Widget Options

### Concept

Each widget gets a settings gear icon (visible on hover, next to the X remove button). Clicking opens a small config panel specific to that widget type.

### Per-Widget Config Examples

| Widget | Configurable Options |
|---|---|
| Tasks | Default filter (active/doing/done), group by project on/off |
| Reminders | Which Apple Reminders lists to show, show/hide completed |
| Calendar | Which Google calendars to display, week start day |
| Events | How many days ahead (7/14/30), show all-day events on/off |
| Notes | Sort order (newest/oldest/pinned first), max visible |
| KPI Cards | Which metric to show (could swap between task counts, finance metrics) |
| Finance Widgets | Which month to display, show trend arrow |
| Email Inbox | Max emails shown, filter (unread only / all) |
| Text Block | Font size, background color |
| Clock | 12h/24h format, show seconds |

### Implementation

- Config stored in `widgetConfigs` (already built — localStorage per profile)
- New `WidgetSettings` component: renders config form based on widget type
- Gear icon appears on hover in widget header area (like the X button)
- Config panel: small popover/dropdown anchored to the gear icon

---

## 4. Additional Widget Ideas

| Widget | Type Key | Description |
|---|---|---|
| Weather | `weather` | Current weather + 3-day forecast (OpenWeatherMap free tier) |
| Bookmarks | `bookmarks` | Quick links grid — configurable URLs |
| Pomodoro | `pomodoro` | Focus timer for tasks |
| Habits | `habits` | Daily habit tracker with streak counting |
| Quick Links | `quick-links` | Shortcuts to Vault sections (financeiro, analytics) |
| Spotify Now Playing | `spotify` | Currently playing + recent tracks (if Spotify API connected) |

---

## Priority Order

1. **Embedded Claude Chat** — highest impact, differentiator. Makes the dashboard genuinely useful as a daily companion. Start with read-only context, add tool use in Phase 2.
2. **Widget Configurable Options** — gear icon + per-widget settings. Foundation for all widget improvements.
3. **Email Integration** — extends existing Google OAuth. High daily utility.
4. **Additional Widgets** — weather, bookmarks, pomodoro — nice polish.

---

## Architecture Notes

### Claude Chat — Cost

**Zero extra cost.** Uses your Claude Max subscription via the Claude Agent SDK (same as your Telegram bot). Runs locally on your Mac.

### Data Flow

```
User types message in Vault chat widget
  → Frontend POST /api/pessoal/chat/ (SSE stream)
  → Django proxies to local chat sidecar (port 5178)
  → Sidecar gathers Vault context via internal API calls
  → Sidecar sends to Claude Agent SDK (local Claude Code session)
  → Claude responds (streaming) → SSE back to frontend
  → Frontend renders markdown response in chat bubble
```

### Architecture Reference

Your Telegram bot (`claude-assistant`) already does this:
- `src/claude/sdk_integration.py` — ClaudeSDKClient wrapper
- `src/claude/session.py` — session management
- `src/claude/facade.py` — high-level interface
- Uses `claude_agent_sdk` package (ClaudeAgentOptions, streaming)

The Vault chat sidecar can reuse the same SDK patterns.

### Security

- No API key needed — uses local Claude Code auth
- Each profile's chat is isolated (separate sessions)
- Financial data in context is read-only
- Tool use (Phase 2) goes through existing authenticated API endpoints

---

## Dependencies

- Claude Agent SDK (`claude_agent_sdk`) — already installed for your Telegram bot
- Claude Code CLI authenticated with Max subscription — already set up
- Existing Google OAuth for Gmail extension
- Existing widget catalog system (just built)
- Existing `/api/analytics/metricas/` and `/api/pessoal/*` endpoints for context
