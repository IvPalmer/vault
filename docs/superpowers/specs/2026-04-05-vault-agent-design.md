# Vault Agent — Design Spec

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this spec.

**Goal:** Turn the existing chat sidecar into a tool-equipped AI assistant for Rafa — capable of reading, creating, editing, and managing her personal organizer, Google Suite, calendar, reminders, and finances through natural Portuguese conversation.

**Primary user:** Rafaella. Agent speaks Brazilian Portuguese, casual tone.

**Architecture:** Enhanced chat sidecar (FastAPI + Claude Agent SDK). Tools call back into Vault's Django REST API. No new services or containers.

---

## Architecture

```
Rafa types in ChatWidget
  -> SSE POST to chat sidecar (/chat)
    -> Claude Agent SDK processes message
      -> Claude decides to call tool (e.g. create_task)
        -> Sidecar executes: POST /api/pessoal/tasks/ via Vault API
        -> Tool result returned to Claude
      -> Claude responds in Portuguese
    -> SSE streams back to ChatWidget
```

### Key constraints

- **Profile scoping**: Every API call includes `X-Profile-ID: {profile_id}` from the chat session. Agent can only access the logged-in user's data.
- **No code access**: Agent cannot read/write local files, source code, configs, or run shell commands.
- **No cross-profile access**: Agent cannot query or modify another profile's data.
- **No financial mutations beyond categorization**: Cannot create transactions, modify balances, or change recurring templates.

### Confirmation flow

Destructive actions (send email, delete anything, remove widget) require confirmation:
1. Claude outputs: "Vou [descrever acao]. Confirma?"
2. Rafa replies "sim" or equivalent
3. Claude executes the tool
4. If Rafa says anything else, Claude cancels

This is enforced in the system prompt — Claude is instructed to never execute destructive tools without explicit confirmation in the preceding user message.

---

## Tool Set

### Level 1 — Read-only

Shipped first. Agent can answer questions with live data.

#### Personal Organizer

| Tool | Parameters | Endpoint |
|------|-----------|----------|
| `list_tasks` | `status?`, `project_id?` | GET /api/pessoal/tasks/ |
| `list_projects` | `status?` | GET /api/pessoal/projects/ |
| `list_notes` | `project_id?` | GET /api/pessoal/notes/ |

#### Calendar & Reminders

| Tool | Parameters | Endpoint |
|------|-----------|----------|
| `get_calendar_events` | `time_min`, `time_max`, `context?` | GET /api/calendar/events/ |
| `get_reminders` | `list_name` | GET /api/home/reminders/ |
| `get_reminder_lists` | — | GET /api/home/reminders/lists/ |

#### Google Suite

| Tool | Parameters | Endpoint |
|------|-----------|----------|
| `search_emails` | `query`, `account_email?`, `limit?` | GET /api/google/gmail/messages/ |
| `read_email` | `message_id`, `account_email?` | GET /api/google/gmail/messages/{id}/ |
| `search_drive` | `query`, `account_email?` | GET /api/google/drive/files/ |
| `read_document` | `document_id`, `account_email?` | GET /api/google/drive/docs/{id}/ |
| `read_spreadsheet` | `spreadsheet_id`, `range?`, `account_email?` | GET /api/google/drive/sheets/{id}/ |

#### Finances

| Tool | Parameters | Endpoint |
|------|-----------|----------|
| `get_finances` | `month_str?` | GET /api/analytics/metricas/ |

### Level 2 — Write tools

Added on top of Level 1. Shipped as second phase.

#### Personal Organizer — Write

| Tool | Parameters | Confirmation? |
|------|-----------|---------------|
| `create_task` | `title`, `due_date?`, `priority?`, `project?`, `notes?` | No |
| `update_task` | `task_id`, `status?`, `title?`, `due_date?`, `priority?`, `project?`, `notes?` | No |
| `delete_task` | `task_id` | **Yes** |
| `create_note` | `title`, `content?`, `project?` | No |
| `delete_note` | `note_id` | **Yes** |
| `create_project` | `name`, `description?`, `color?` | No |

#### Google Suite — Write

| Tool | Parameters | Confirmation? |
|------|-----------|---------------|
| `send_email` | `to`, `subject`, `body`, `account_email?` | **Yes** |
| `draft_email` | `to`, `subject`, `body`, `account_email?` | No |
| `trash_email` | `message_id`, `account_email?` | **Yes** |
| `create_document` | `title`, `content?`, `account_email?` | No |
| `edit_document` | `document_id`, `append_text?`, `find_replace?` (list of {find, replace}), `account_email?` | No |
| `create_spreadsheet` | `title`, `account_email?` | No |
| `edit_spreadsheet` | `spreadsheet_id`, `range`, `values`, `account_email?` | No |

#### Calendar & Reminders — Write

| Tool | Parameters | Confirmation? |
|------|-----------|---------------|
| `create_calendar_event` | `title`, `start`, `end`, `description?`, `account_id?` | No |
| `add_reminder` | `name`, `list_name?` | No |
| `complete_reminder` | `name`, `list_name` | No |

#### Dashboard

| Tool | Parameters | Confirmation? |
|------|-----------|---------------|
| `add_widget` | `widget_type` | No |
| `remove_widget` | `widget_id` | **Yes** |

#### Finances — Write

| Tool | Parameters | Confirmation? |
|------|-----------|---------------|
| `categorize_transaction` | `transaction_id`, `category_id`, `subcategory_id?` | No |

---

## System Prompt

The system prompt sets the agent's behavior:

```
Voce e a assistente pessoal da {profile_name} no Vault.
Responda sempre em portugues brasileiro, tom casual e direto.
Voce tem acesso a tarefas, notas, projetos, calendario, lembretes,
emails, Google Drive, e dados financeiros.

Regras:
- Nunca execute acoes destrutivas (enviar email, deletar, remover widget)
  sem perguntar "Confirma?" e receber "sim" da usuaria.
- Nunca acesse arquivos do sistema, codigo fonte, ou configuracoes.
- Nunca acesse dados de outro perfil.
- Quando a usuaria pedir algo que voce nao pode fazer, explique por que.
- Seja concisa — respostas curtas, sem enrolacao.
- Use as tools disponiveis para buscar dados ao vivo antes de responder.
  Nao invente informacoes.
```

The system prompt also receives injected context (already built in the sidecar):
- Current date/time
- Profile metadata
- Recent tasks, upcoming events, unread emails count

---

## Implementation Phases

### Phase 1 — Level 1 (read-only)

**Files to modify:**
- `chat-sidecar/server.py` — add tool definitions to Claude Agent SDK config, implement tool execution functions
- `src/components/widgets/ChatWidget.jsx` — show tool activity indicator ("Buscando emails...")

**Steps:**
1. Define tool schemas as Claude tool_definitions JSON
2. Implement `execute_tool(name, params, profile_id)` dispatcher function
3. Each tool function calls the Vault API via httpx with `X-Profile-ID` header
4. Tool results returned to Claude as tool_result messages
5. Update system prompt with Portuguese persona and tool usage guidelines
6. ChatWidget: detect `tool_use` blocks in SSE stream, show activity indicator

### Phase 2 — Level 2 (write tools)

**Files to modify:**
- `chat-sidecar/server.py` — add write tool definitions and execution functions
- `src/components/widgets/ChatWidget.jsx` — add confirmation UI

**Steps:**
1. Add write tool definitions to the tool registry
2. Implement confirmation detection — check if preceding user message contains confirmation
3. For destructive tools: if no confirmation, return "needs_confirmation" result to Claude, which prompts Rafa
4. Add write tool execution functions (POST/PATCH/DELETE calls)
5. Audit logging: append to a log file with timestamp, profile, tool, params, result
6. ChatWidget: render confirmation prompts distinctly (e.g. highlighted border)

### Phase 3 — Polish

- **Semantic memory**: Store conversation summaries and user preferences in a DB model, inject into system prompt
- **Rich previews**: ChatWidget renders inline cards for emails, docs, events returned by tools
- **Proactive suggestions**: On page load, agent checks for overdue tasks, upcoming events, and surfaces a greeting with actionable suggestions

---

## Safety Model

| Rule | Enforcement |
|------|-------------|
| No code/config changes | No tools exist for file system access. Sidecar has no fs write capability. |
| No cross-profile | All API calls use session's profile_id. Django middleware enforces. |
| No financial mutations (beyond categorization) | No tools for transaction creation, balance changes, or recurring template edits. |
| Confirmation on destructive actions | System prompt + tool execution checks preceding message for confirmation. |
| Error containment | API errors returned as tool results. Claude explains in Portuguese. No stack traces exposed. |

---

## Google Account Selection

Rafa has 4 Google accounts. Tools that access Google Suite accept an optional `account_email` parameter. If omitted, the agent uses the first connected account. Claude can ask Rafa which account to use when ambiguous.

Available accounts (from DB):
- rafaellarezendegalvao@gmail.com (primary)
- cinebrasiliaprogramacao@gmail.com
- rafaelarezend@gmail.com
- rafaellagalvao@sempreceub.com

---

## Chat Widget Updates

The ChatWidget (`src/components/widgets/ChatWidget.jsx`) needs minor updates:

1. **Tool activity indicator**: When the SSE stream contains a tool_use block, show a subtle "Buscando..." or "Criando tarefa..." message before the final response arrives.
2. **Confirmation styling**: When Claude asks for confirmation, render the message with a distinct style (e.g. accent border) so Rafa knows action is pending.
3. No other UI changes — the chat widget remains a floating panel.
