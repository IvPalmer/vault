# Vault Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing chat sidecar into a tool-equipped AI assistant for Rafa by adding an in-process MCP server that exposes Vault tools to Claude.

**Architecture:** The sidecar's `ClaudeAgentOptions` gains an `mcp_servers` entry pointing to an in-process Python MCP server. This MCP server exposes tools that call the Vault Django API via httpx. Claude sees these as callable tools and uses them to answer questions and perform actions.

**Tech Stack:** Python MCP SDK (`mcp`), Claude Agent SDK (`claude_agent_sdk`), FastAPI (existing sidecar), httpx (existing HTTP client)

---

## File Structure

```
chat-sidecar/
  server.py              — MODIFY: add MCP server to ClaudeAgentOptions, update system prompt
  vault_tools.py          — CREATE: MCP server with all Vault tool definitions and handlers
  tool_helpers.py         — CREATE: shared httpx client, API call helper, confirmation logic
```

```
src/components/widgets/
  ChatWidget.jsx          — MODIFY: tool activity indicator, confirmation styling
  ChatWidget.module.css   — MODIFY: styles for tool activity and confirmation
```

---

### Task 1: Install MCP Python SDK

**Files:**
- Modify: `chat-sidecar/requirements.txt`

- [ ] **Step 1: Add mcp dependency**

```
fastapi
uvicorn[standard]
claude-agent-sdk
httpx
mcp
```

- [ ] **Step 2: Install**

Run: `cd chat-sidecar && pip install -r requirements.txt`
Expected: Successfully installed mcp

- [ ] **Step 3: Verify import works**

Run: `python3 -c "from mcp.server import Server; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add chat-sidecar/requirements.txt
git commit -m "chore: add mcp dependency for vault agent tools"
```

---

### Task 2: Create tool helpers module

**Files:**
- Create: `chat-sidecar/tool_helpers.py`

This module provides the shared HTTP client for calling Vault APIs and a helper for building API URLs.

- [ ] **Step 1: Create tool_helpers.py**

```python
"""
Shared helpers for Vault MCP tools.
Provides httpx client, API base URL, and request helper.
"""
import httpx
import os

VAULT_API = os.environ.get("VAULT_API_URL", "http://127.0.0.1:8001/api")
REMINDERS_API = os.environ.get("REMINDERS_API_URL", "http://127.0.0.1:5177/api/home/reminders")

# Shared async client (reused across tool calls)
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def vault_get(path: str, profile_id: str, params: dict | None = None) -> dict:
    """GET request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.get(
        f"{VAULT_API}{path}",
        headers={"X-Profile-ID": profile_id},
        params=params or {},
    )
    resp.raise_for_status()
    return resp.json()


async def vault_post(path: str, profile_id: str, data: dict | None = None) -> dict:
    """POST request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.post(
        f"{VAULT_API}{path}",
        headers={"X-Profile-ID": profile_id, "Content-Type": "application/json"},
        json=data or {},
    )
    resp.raise_for_status()
    return resp.json()


async def vault_patch(path: str, profile_id: str, data: dict) -> dict:
    """PATCH request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.patch(
        f"{VAULT_API}{path}",
        headers={"X-Profile-ID": profile_id, "Content-Type": "application/json"},
        json=data,
    )
    resp.raise_for_status()
    return resp.json()


async def vault_delete(path: str, profile_id: str) -> dict | None:
    """DELETE request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.delete(
        f"{VAULT_API}{path}",
        headers={"X-Profile-ID": profile_id},
    )
    resp.raise_for_status()
    if resp.status_code == 204:
        return None
    return resp.json()


async def reminders_get(path: str, params: dict | None = None) -> dict:
    """GET request to reminders sidecar."""
    client = get_client()
    resp = await client.get(f"{REMINDERS_API}{path}", params=params or {})
    resp.raise_for_status()
    return resp.json()


async def reminders_post(path: str, data: dict) -> dict:
    """POST request to reminders sidecar."""
    client = get_client()
    resp = await client.post(
        f"{REMINDERS_API}{path}",
        headers={"Content-Type": "application/json"},
        json=data,
    )
    resp.raise_for_status()
    return resp.json()
```

- [ ] **Step 2: Verify it loads**

Run: `cd chat-sidecar && python3 -c "from tool_helpers import VAULT_API; print(VAULT_API)"`
Expected: `http://127.0.0.1:8001/api`

- [ ] **Step 3: Commit**

```bash
git add chat-sidecar/tool_helpers.py
git commit -m "feat(agent): add tool helpers — shared httpx client for Vault API"
```

---

### Task 3: Create MCP server with Level 1 read tools

**Files:**
- Create: `chat-sidecar/vault_tools.py`

This is the core MCP server. Each tool is a decorated function that calls the Vault API via tool_helpers.

- [ ] **Step 1: Create vault_tools.py with read-only tools**

```python
"""
Vault MCP Server — exposes Vault tools to Claude via MCP protocol.

Level 1: Read-only tools (tasks, notes, projects, calendar, reminders, email, drive, finances)
Level 2: Write tools (create/update/delete tasks, notes, send email, edit docs, etc.)
"""
import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from tool_helpers import (
    vault_get, vault_post, vault_patch, vault_delete,
    reminders_get, reminders_post,
)

# The profile_id is set per-session before tools are called
_current_profile_id: str | None = None


def set_profile(profile_id: str):
    """Set the active profile for subsequent tool calls."""
    global _current_profile_id
    _current_profile_id = profile_id


def _pid() -> str:
    if not _current_profile_id:
        raise ValueError("No profile set — call set_profile() first")
    return _current_profile_id


def create_vault_mcp_server() -> Server:
    """Create and configure the Vault MCP server."""
    server = Server("vault-tools")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            # ── Level 1: Read ──
            Tool(
                name="list_tasks",
                description="List personal tasks. Returns title, status, due_date, priority, project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["todo", "doing", "done"], "description": "Filter by status"},
                        "project_id": {"type": "string", "description": "Filter by project UUID"},
                    },
                },
            ),
            Tool(
                name="list_projects",
                description="List personal projects with name, status, color, task count.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="list_notes",
                description="List personal notes with title, content preview, project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Filter by project UUID"},
                    },
                },
            ),
            Tool(
                name="get_calendar_events",
                description="Get calendar events in a date range. Returns title, start, end, location, calendar name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "time_min": {"type": "string", "description": "Start date YYYY-MM-DD (required)"},
                        "time_max": {"type": "string", "description": "End date YYYY-MM-DD (required)"},
                    },
                    "required": ["time_min", "time_max"],
                },
            ),
            Tool(
                name="get_reminders",
                description="Get reminders from an Apple Reminders list.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "list_name": {"type": "string", "description": "Reminder list name (required)"},
                    },
                    "required": ["list_name"],
                },
            ),
            Tool(
                name="get_reminder_lists",
                description="List all available Apple Reminder lists.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="search_emails",
                description="Search Gmail messages. Returns subject, from, date, snippet, is_unread.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Gmail search query (e.g. 'is:unread', 'from:boss', 'subject:meeting')"},
                        "account_email": {"type": "string", "description": "Which Google account to search. Omit for default."},
                        "limit": {"type": "integer", "description": "Max results (default 10)"},
                    },
                },
            ),
            Tool(
                name="read_email",
                description="Read full content of a specific email by message ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID (required)"},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["message_id"],
                },
            ),
            Tool(
                name="search_drive",
                description="Search Google Drive files. Returns file name, type, modified date, id.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (required)"},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="read_document",
                description="Read content of a Google Doc by document ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "document_id": {"type": "string", "description": "Google Doc ID (required)"},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["document_id"],
                },
            ),
            Tool(
                name="read_spreadsheet",
                description="Read data from a Google Sheet. Returns cell values.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "spreadsheet_id": {"type": "string", "description": "Google Sheet ID (required)"},
                        "range": {"type": "string", "description": "Cell range e.g. 'Sheet1!A1:D10'. Omit for all data."},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["spreadsheet_id"],
                },
            ),
            Tool(
                name="get_finances",
                description="Get financial summary for a month: saldo, income, expenses, fatura, savings rate.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "month_str": {"type": "string", "description": "Month in YYYY-MM format. Omit for current month."},
                    },
                },
            ),
            # ── Level 2: Write ──
            Tool(
                name="create_task",
                description="Create a new personal task.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Task title (required)"},
                        "due_date": {"type": "string", "description": "Due date YYYY-MM-DD"},
                        "priority": {"type": "integer", "enum": [0, 1, 2, 3], "description": "0=none, 1=low, 2=medium, 3=high"},
                        "project": {"type": "string", "description": "Project UUID"},
                        "notes": {"type": "string", "description": "Task notes"},
                    },
                    "required": ["title"],
                },
            ),
            Tool(
                name="update_task",
                description="Update an existing task's status, title, due date, priority, or notes.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task UUID (required)"},
                        "status": {"type": "string", "enum": ["todo", "doing", "done"]},
                        "title": {"type": "string"},
                        "due_date": {"type": "string", "description": "YYYY-MM-DD or null to clear"},
                        "priority": {"type": "integer", "enum": [0, 1, 2, 3]},
                        "notes": {"type": "string"},
                        "project": {"type": "string", "description": "Project UUID or null to unassign"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="delete_task",
                description="DESTRUCTIVE: Delete a task permanently. Always ask for confirmation before calling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string", "description": "Task UUID (required)"},
                    },
                    "required": ["task_id"],
                },
            ),
            Tool(
                name="create_note",
                description="Create a new personal note.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title (required)"},
                        "content": {"type": "string", "description": "Note content (markdown)"},
                        "project": {"type": "string", "description": "Project UUID"},
                    },
                    "required": ["title"],
                },
            ),
            Tool(
                name="delete_note",
                description="DESTRUCTIVE: Delete a note permanently. Always ask for confirmation before calling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "note_id": {"type": "string", "description": "Note UUID (required)"},
                    },
                    "required": ["note_id"],
                },
            ),
            Tool(
                name="create_project",
                description="Create a new project to organize tasks and notes.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Project name (required)"},
                        "description": {"type": "string"},
                        "color": {"type": "string", "description": "Hex color e.g. '#4caf50'"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="send_email",
                description="DESTRUCTIVE: Send an email via Gmail. Always ask for confirmation before calling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email (required)"},
                        "subject": {"type": "string", "description": "Email subject (required)"},
                        "body": {"type": "string", "description": "Email body text (required)"},
                        "account_email": {"type": "string", "description": "Send from this Google account"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            Tool(
                name="draft_email",
                description="Create a Gmail draft (does not send).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string", "description": "Recipient email (required)"},
                        "subject": {"type": "string", "description": "Email subject (required)"},
                        "body": {"type": "string", "description": "Email body text (required)"},
                        "account_email": {"type": "string", "description": "Google account"},
                    },
                    "required": ["to", "subject", "body"],
                },
            ),
            Tool(
                name="trash_email",
                description="DESTRUCTIVE: Move an email to trash. Always ask for confirmation before calling.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message_id": {"type": "string", "description": "Gmail message ID (required)"},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["message_id"],
                },
            ),
            Tool(
                name="create_calendar_event",
                description="Create a new calendar event.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Event title (required)"},
                        "start": {"type": "string", "description": "Start datetime ISO format (required)"},
                        "end": {"type": "string", "description": "End datetime ISO format (required)"},
                        "description": {"type": "string"},
                    },
                    "required": ["title", "start", "end"],
                },
            ),
            Tool(
                name="add_reminder",
                description="Add an item to an Apple Reminders list.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Reminder text (required)"},
                        "list_name": {"type": "string", "description": "List name (default: first list)"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="complete_reminder",
                description="Mark an Apple Reminder as completed.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Reminder name (required)"},
                        "list_name": {"type": "string", "description": "List name (required)"},
                    },
                    "required": ["name", "list_name"],
                },
            ),
            Tool(
                name="categorize_transaction",
                description="Set the category of a financial transaction.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "transaction_id": {"type": "string", "description": "Transaction UUID (required)"},
                        "category_id": {"type": "string", "description": "Category UUID (required)"},
                        "subcategory_id": {"type": "string", "description": "Subcategory UUID (optional)"},
                    },
                    "required": ["transaction_id", "category_id"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            result = await _execute_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except httpx.HTTPStatusError as e:
            error_body = e.response.text[:500] if e.response else str(e)
            return [TextContent(type="text", text=json.dumps({"error": f"API {e.response.status_code}: {error_body}"}, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

    return server


async def _execute_tool(name: str, args: dict) -> dict | list | None:
    """Route tool call to the appropriate Vault API endpoint."""
    pid = _pid()

    # ── Level 1: Read ──
    if name == "list_tasks":
        params = {}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("project_id"):
            params["project"] = args["project_id"]
        data = await vault_get("/pessoal/tasks/", pid, params)
        return data.get("results", data)

    if name == "list_projects":
        data = await vault_get("/pessoal/projects/", pid)
        return data.get("results", data)

    if name == "list_notes":
        params = {}
        if args.get("project_id"):
            params["project"] = args["project_id"]
        data = await vault_get("/pessoal/notes/", pid, params)
        return data.get("results", data)

    if name == "get_calendar_events":
        params = {"time_min": args["time_min"], "time_max": args["time_max"], "context": "personal"}
        return await vault_get("/calendar/events/", pid, params)

    if name == "get_reminders":
        return await reminders_get(f"/?list={args['list_name']}")

    if name == "get_reminder_lists":
        return await reminders_get("/lists/?all=true")

    if name == "search_emails":
        params = {}
        if args.get("query"):
            params["q"] = args["query"]
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        if args.get("limit"):
            params["limit"] = str(args["limit"])
        return await vault_get("/google/gmail/messages/", pid, params)

    if name == "read_email":
        params = {}
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        return await vault_get(f"/google/gmail/messages/{args['message_id']}/", pid, params)

    if name == "search_drive":
        params = {"q": args["query"]}
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        return await vault_get("/google/drive/files/", pid, params)

    if name == "read_document":
        params = {}
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        return await vault_get(f"/google/drive/docs/{args['document_id']}/", pid, params)

    if name == "read_spreadsheet":
        params = {}
        if args.get("range"):
            params["range"] = args["range"]
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        return await vault_get(f"/google/drive/sheets/{args['spreadsheet_id']}/", pid, params)

    if name == "get_finances":
        params = {}
        if args.get("month_str"):
            params["month_str"] = args["month_str"]
        return await vault_get("/analytics/metricas/", pid, params)

    # ── Level 2: Write ──
    if name == "create_task":
        data = {"title": args["title"]}
        for key in ("due_date", "priority", "project", "notes"):
            if args.get(key) is not None:
                data[key] = args[key]
        return await vault_post("/pessoal/tasks/", pid, data)

    if name == "update_task":
        task_id = args.pop("task_id")
        data = {k: v for k, v in args.items() if v is not None}
        return await vault_patch(f"/pessoal/tasks/{task_id}/", pid, data)

    if name == "delete_task":
        return await vault_delete(f"/pessoal/tasks/{args['task_id']}/", pid)

    if name == "create_note":
        data = {"title": args["title"]}
        for key in ("content", "project"):
            if args.get(key):
                data[key] = args[key]
        return await vault_post("/pessoal/notes/", pid, data)

    if name == "delete_note":
        return await vault_delete(f"/pessoal/notes/{args['note_id']}/", pid)

    if name == "create_project":
        data = {"name": args["name"]}
        for key in ("description", "color"):
            if args.get(key):
                data[key] = args[key]
        return await vault_post("/pessoal/projects/", pid, data)

    if name == "send_email":
        data = {"to": args["to"], "subject": args["subject"], "body": args["body"]}
        if args.get("account_email"):
            data["account_email"] = args["account_email"]
        return await vault_post("/google/gmail/send/", pid, data)

    if name == "draft_email":
        data = {"to": args["to"], "subject": args["subject"], "body": args["body"], "draft": True}
        if args.get("account_email"):
            data["account_email"] = args["account_email"]
        return await vault_post("/google/gmail/send/", pid, data)

    if name == "trash_email":
        params = {}
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        return await vault_post(f"/google/gmail/trash/{args['message_id']}/", pid)

    if name == "create_calendar_event":
        data = {"title": args["title"], "start": args["start"], "end": args["end"]}
        if args.get("description"):
            data["description"] = args["description"]
        return await vault_post("/calendar/add-event/", pid, data)

    if name == "add_reminder":
        data = {"name": args["name"]}
        if args.get("list_name"):
            data["list"] = args["list_name"]
        return await reminders_post("/add/", data)

    if name == "complete_reminder":
        return await reminders_post("/complete/", {"name": args["name"], "list": args["list_name"]})

    if name == "categorize_transaction":
        data = {"category": args["category_id"]}
        if args.get("subcategory_id"):
            data["subcategory"] = args["subcategory_id"]
        return await vault_patch(f"/transactions/{args['transaction_id']}/", pid, data)

    return {"error": f"Unknown tool: {name}"}
```

- [ ] **Step 2: Verify it loads**

Run: `cd chat-sidecar && python3 -c "from vault_tools import create_vault_mcp_server; s = create_vault_mcp_server(); print(f'Server: {s.name}')"`
Expected: `Server: vault-tools`

- [ ] **Step 3: Commit**

```bash
git add chat-sidecar/vault_tools.py
git commit -m "feat(agent): MCP server with read + write tools for Vault"
```

---

### Task 4: Wire MCP server into chat sidecar

**Files:**
- Modify: `chat-sidecar/server.py`

Connect the MCP server to `ClaudeAgentOptions` so Claude can use the tools.

- [ ] **Step 1: Add imports at top of server.py**

After the existing `from claude_agent_sdk import ...` block (around line 31), add:

```python
from vault_tools import create_vault_mcp_server, set_profile
```

- [ ] **Step 2: Create the MCP server instance**

After `MAX_MEMORY = 20` (around line 49), add:

```python
# Vault MCP tools server (in-process, no separate process needed)
_vault_mcp = create_vault_mcp_server()
```

- [ ] **Step 3: Update _stream_chat to set profile and add MCP server**

In `_stream_chat()`, before the `options = ClaudeAgentOptions(...)` block (around line 329), add the profile setup:

```python
    # Set active profile for MCP tools
    set_profile(req.profile_id)
```

Then modify the `ClaudeAgentOptions` to include the MCP server:

Replace the existing options block:
```python
    options = ClaudeAgentOptions(
        max_turns=10,
        cwd="/Users/palmer/Work/Dev/Vault",
        system_prompt=system_prompt,
        include_partial_messages=False,
    )
```

With:
```python
    options = ClaudeAgentOptions(
        max_turns=10,
        cwd="/Users/palmer/Work/Dev/Vault",
        system_prompt=system_prompt,
        include_partial_messages=False,
        mcp_servers={"vault-tools": {"type": "sdk", "name": "vault-tools", "instance": _vault_mcp}},
        permission_mode="bypassPermissions",
        allowed_tools=[
            "mcp__vault-tools__list_tasks",
            "mcp__vault-tools__list_projects",
            "mcp__vault-tools__list_notes",
            "mcp__vault-tools__get_calendar_events",
            "mcp__vault-tools__get_reminders",
            "mcp__vault-tools__get_reminder_lists",
            "mcp__vault-tools__search_emails",
            "mcp__vault-tools__read_email",
            "mcp__vault-tools__search_drive",
            "mcp__vault-tools__read_document",
            "mcp__vault-tools__read_spreadsheet",
            "mcp__vault-tools__get_finances",
            "mcp__vault-tools__create_task",
            "mcp__vault-tools__update_task",
            "mcp__vault-tools__delete_task",
            "mcp__vault-tools__create_note",
            "mcp__vault-tools__delete_note",
            "mcp__vault-tools__create_project",
            "mcp__vault-tools__send_email",
            "mcp__vault-tools__draft_email",
            "mcp__vault-tools__trash_email",
            "mcp__vault-tools__create_calendar_event",
            "mcp__vault-tools__add_reminder",
            "mcp__vault-tools__complete_reminder",
            "mcp__vault-tools__categorize_transaction",
        ],
        disallowed_tools=["Bash", "Edit", "Write", "Read", "Glob", "Grep", "Agent", "NotebookEdit"],
    )
```

- [ ] **Step 4: Update CORS to allow Tailscale origin**

Replace:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

With:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "https://localhost:5175", "https://raphaels-mac-studio.tail5d4d09.ts.net:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 5: Commit**

```bash
git add chat-sidecar/server.py
git commit -m "feat(agent): wire MCP tools into chat sidecar — Claude can now use Vault tools"
```

---

### Task 5: Update system prompt for agent behavior

**Files:**
- Modify: `chat-sidecar/server.py`

- [ ] **Step 1: Replace _build_system_prompt function**

Replace the entire `_build_system_prompt` function (lines ~250-293) with:

```python
def _build_system_prompt(profile_id: str, profile_name: str, context: str) -> str:
    """Build a rich system prompt with profile awareness, context, and tool instructions."""
    meta = PROFILE_META.get(profile_id)

    if meta:
        personality = meta["lang_hint"]
        who = meta["context"]
    else:
        personality = RAFA_HINT
        who = f"{profile_name} is a Vault user."

    # Include conversation memory summary
    memory = _memory.get(profile_id, [])
    memory_section = ""
    if memory:
        recent = memory[-6:]  # last 3 exchanges
        mem_lines = []
        for m in recent:
            role = "User" if m["role"] == "user" else "Assistant"
            content = m["content"][:200]
            mem_lines.append(f"  {role}: {content}")
        memory_section = "\n\nCONVERSA RECENTE:\n" + "\n".join(mem_lines)

    return f"""Voce e a assistente pessoal de {profile_name} no Vault, um app de organizacao pessoal e financas.

QUEM VOCE ESTA FALANDO:
{who}

PERSONALIDADE:
{personality}
Seja concisa, direta e calorosa. Use markdown quando ajudar (negrito, listas).
Responda SEMPRE em portugues brasileiro.

FERRAMENTAS DISPONIVEIS:
Voce tem acesso a ferramentas (tools) para consultar e modificar dados ao vivo.
USE AS FERRAMENTAS para buscar informacoes antes de responder — nunca invente dados.

Ferramentas de leitura: list_tasks, list_projects, list_notes, get_calendar_events,
get_reminders, get_reminder_lists, search_emails, read_email, search_drive,
read_document, read_spreadsheet, get_finances.

Ferramentas de escrita: create_task, update_task, delete_task, create_note, delete_note,
create_project, send_email, draft_email, trash_email, create_calendar_event,
add_reminder, complete_reminder, categorize_transaction.

REGRAS IMPORTANTES:
1. ACOES DESTRUTIVAS (send_email, delete_task, delete_note, trash_email):
   SEMPRE pergunte "Confirma?" e espere a usuaria responder "sim" antes de executar.
   Nunca execute essas acoes sem confirmacao explicita.
2. Nunca acesse arquivos do sistema, codigo fonte, ou configuracoes do servidor.
3. Use as ferramentas para buscar dados atualizados — o contexto abaixo pode estar desatualizado.
4. Quando a usuaria pedir algo que voce nao pode fazer, explique o motivo.
5. Para emails: a usuaria tem multiplas contas Google. Pergunte de qual conta
   enviar/buscar quando nao estiver claro pelo contexto.

DATA ATUAL: {datetime.now().strftime('%A, %d de %B de %Y')}

{context}{memory_section}"""
```

- [ ] **Step 2: Commit**

```bash
git add chat-sidecar/server.py
git commit -m "feat(agent): update system prompt — Portuguese persona with tool usage rules"
```

---

### Task 6: Update ChatWidget for tool activity

**Files:**
- Modify: `src/components/widgets/ChatWidget.jsx`
- Modify: `src/components/widgets/ChatWidget.module.css`

The Claude Agent SDK handles tool calls internally — the SSE stream from the sidecar already waits for the full response (after all tool calls complete). The sidecar's `_stream_chat` collects the `last_assistant_text` from the final `AssistantMessage`. So tool activity is invisible to the frontend — it just sees a longer response time.

We need to add a better typing indicator that shows while tools are running (the response may take 5-10 seconds with multiple tool calls).

- [ ] **Step 1: Update ChatWidget.jsx — improve typing indicator**

In ChatWidget.jsx, find the section where `isStreaming` is true and the typing dots are shown. The current code adds a placeholder assistant message. Update it to show a more descriptive message. Find the `handleSend` function and after the streaming placeholder message is added, update the typing text:

Find this pattern (where the assistant streaming placeholder is added):
```javascript
setMessages(prev => [...prev, { role: 'assistant', content: '' }])
```

And after it, the streaming reads data. The typing indicator is already shown via CSS when `content` is empty. This is sufficient — the dots animation plays while the agent processes tools internally.

No code change needed here — the existing typing indicator works. Skip to styling.

- [ ] **Step 2: Add confirmation message styling to ChatWidget.module.css**

At the end of `ChatWidget.module.css`, add:

```css
/* Confirmation messages from agent */
.confirmMessage {
  border-left: 3px solid var(--color-accent) !important;
  background: rgba(184, 101, 48, 0.06) !important;
}
```

- [ ] **Step 3: Update message rendering in ChatWidget.jsx to detect confirmation**

In the message rendering section (where `renderContent` is called for each message), wrap the assistant message div to detect confirmation patterns. Find where assistant messages are rendered and add a class check:

In the `messagesArea` div where messages are mapped, find the assistant message `<div>` and update:

```jsx
<div
  key={i}
  className={`${styles.message} ${m.role === 'user' ? styles.messageUser : styles.messageAssistant} ${
    m.role === 'assistant' && m.content && /confirma\??/i.test(m.content) ? styles.confirmMessage : ''
  }`}
>
```

- [ ] **Step 4: Commit**

```bash
git add src/components/widgets/ChatWidget.jsx src/components/widgets/ChatWidget.module.css
git commit -m "feat(agent): confirmation styling in ChatWidget"
```

---

### Task 7: Update sidecar CORS and ChatWidget URL for HTTPS

**Files:**
- Modify: `src/components/widgets/ChatWidget.jsx`

- [ ] **Step 1: Update SIDECAR_URL in ChatWidget.jsx**

The chat sidecar runs on port 5178. Currently hardcoded as `http://${window.location.hostname}:5178`. Since the page is served over HTTPS, the fetch will work if the sidecar is on HTTP localhost (same-origin exception). But for Rafa accessing via Tailscale, the browser will block mixed content.

Update the `SIDECAR_URL` line (line ~14):

```javascript
const SIDECAR_URL = window.location.protocol === 'https:'
  ? `https://${window.location.hostname}:5178`
  : `http://${window.location.hostname}:5178`
```

Note: The chat sidecar will also need HTTPS. For now it works via the Vite proxy if we add a proxy rule. Add to `vite.config.js` proxy section:

Actually, the simplest fix: route chat through the Vite proxy like we do for reminders.

In ChatWidget.jsx, change:
```javascript
const SIDECAR_URL = `http://${window.location.hostname}:5178`
```

To:
```javascript
const SIDECAR_URL = ''  // use Vite proxy at /chat
```

And update the fetch URLs from `${SIDECAR_URL}/chat` to `/sidecar/chat` and `${SIDECAR_URL}/clear` to `/sidecar/clear`.

Then add to `vite.config.js` proxy section (before the `/api` catch-all):
```javascript
'/sidecar': {
    target: 'http://127.0.0.1:5178',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/sidecar/, ''),
},
```

- [ ] **Step 2: Commit**

```bash
git add src/components/widgets/ChatWidget.jsx vite.config.js
git commit -m "feat(agent): route chat through Vite proxy for HTTPS compatibility"
```

---

### Task 8: Test the agent end-to-end

**Files:** None (manual testing)

- [ ] **Step 1: Restart the chat sidecar**

```bash
cd chat-sidecar && pkill -f "uvicorn server:app" || true
uvicorn server:app --host 0.0.0.0 --port 5178 &
```

- [ ] **Step 2: Test read tools**

Open the chat widget on the Pessoal page. Send these messages and verify responses:

1. "Quais sao minhas tarefas?" — should call `list_tasks` and return real tasks
2. "Tenho eventos essa semana?" — should call `get_calendar_events` with current week range
3. "Busca emails nao lidos" — should call `search_emails` with `is:unread`
4. "Qual meu saldo esse mes?" — should call `get_finances` and return metricas summary

- [ ] **Step 3: Test write tools**

1. "Cria uma tarefa: comprar leite, vencimento amanha" — should call `create_task`
2. "Adiciona no lembrete R&R Compras: papel toalha" — should call `add_reminder`
3. "Deleta a tarefa comprar leite" — should ask "Confirma?" first, then delete after "sim"

- [ ] **Step 4: Test safety**

1. "Envia um email para teste@teste.com dizendo oi" — should ask confirmation before sending
2. Verify agent cannot access file system or run commands
3. Switch to Palmer's profile — verify agent only sees Palmer's data

- [ ] **Step 5: Commit any fixes found during testing**

```bash
git add -A
git commit -m "fix(agent): testing fixes"
```

---

## Self-Review

**Spec coverage check:**
- Architecture (enhanced sidecar with MCP): Task 3-4 ✓
- Tool set Level 1 (read): Task 3 ✓
- Tool set Level 2 (write): Task 3 ✓
- System prompt (Portuguese, rules): Task 5 ✓
- Confirmation flow: Task 5 (system prompt rules) + Task 3 (destructive tool descriptions) ✓
- Safety/containment: Task 4 (disallowed_tools, permission_mode) ✓
- ChatWidget updates: Task 6 ✓
- HTTPS compatibility: Task 7 ✓
- Google account selection: Task 3 (account_email param on all Google tools) ✓
- Profile scoping: Task 2 (X-Profile-ID header) + Task 4 (set_profile) ✓

**Placeholder scan:** No TBD/TODO found. All code blocks are complete.

**Type consistency:** `set_profile`/`_pid()`/`_current_profile_id` used consistently. Tool names match between `list_tools()`, `_execute_tool()`, and `allowed_tools` list.
