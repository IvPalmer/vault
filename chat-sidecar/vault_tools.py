"""
Vault MCP Server — exposes Vault tools to Claude via MCP protocol.

Level 1: Read-only tools (tasks, notes, projects, calendar, reminders, email, drive, finances)
Level 2: Write tools (create/update/delete tasks, notes, send email, edit docs, etc.)
"""
import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from tool_helpers import (
    vault_get, vault_post, vault_put, vault_patch, vault_delete,
    reminders_get, reminders_post,
    get_client, VAULT_API,
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
                name="update_spreadsheet",
                description="Write data to a Google Sheet. Specify range (e.g. 'Sheet1!A1:C3') and values as 2D array.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "spreadsheet_id": {"type": "string", "description": "Google Sheet ID (required)"},
                        "range": {"type": "string", "description": "Cell range e.g. 'Sheet1!A1:C3' (required)"},
                        "values": {"type": "array", "description": "2D array of values e.g. [['A1','B1'],['A2','B2']] (required)", "items": {"type": "array"}},
                        "account_email": {"type": "string", "description": "Google account email"},
                    },
                    "required": ["spreadsheet_id", "range", "values"],
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
            # ── Financial Intelligence ──
            Tool(
                name="get_transactions",
                description="Search transactions. Filter by month, category, description keyword, account. Returns date, amount, description, category, account.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "month_str": {"type": "string", "description": "Month YYYY-MM (required)"},
                        "search": {"type": "string", "description": "Keyword search in description"},
                        "category": {"type": "string", "description": "Category name filter"},
                        "account_id": {"type": "string", "description": "Account UUID filter"},
                        "limit": {"type": "integer", "description": "Max results (default 50)"},
                    },
                    "required": ["month_str"],
                },
            ),
            Tool(
                name="get_spending_trends",
                description="Get spending trends by category over months. Returns per-category totals.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "months": {"type": "integer", "description": "Number of months to look back (default 3)"},
                    },
                },
            ),
            Tool(
                name="get_projection",
                description="Get financial projection for upcoming months: projected balance, income, expenses, investment, fatura per month.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_recurring",
                description="Get recurring expenses/income for a month: fixo (bills), investimento, cartao (CC). Shows expected vs actual.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "month_str": {"type": "string", "description": "Month YYYY-MM. Omit for current month."},
                    },
                },
            ),
            Tool(
                name="get_categories",
                description="List all spending categories and subcategories with their IDs.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_accounts",
                description="List all bank accounts with their IDs, names, and types.",
                inputSchema={"type": "object", "properties": {}},
            ),
            # ── Dashboard / Widget Management ──
            Tool(
                name="get_dashboard",
                description="Get the current dashboard state: tabs, widgets, and their positions. Returns the full layout.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="add_widget",
                description="Add a built-in widget to a dashboard tab. Built-in types: kpi-hoje, kpi-atrasadas, kpi-ativas, kpi-projetos, capture, projects, tasks, reminders, calendar, events, notes, text-block, clock, greeting, email-inbox, drive-files, fin-saldo, fin-sobra, fin-fatura, custom. Grid is 12 columns wide. For fully custom widgets use create_custom_widget instead.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tab_id": {"type": "string", "description": "Tab ID to add widget to. Omit for active/first tab."},
                        "type": {"type": "string", "description": "Widget type (required)"},
                        "x": {"type": "integer", "description": "Grid column (0-11). Omit for auto-placement."},
                        "y": {"type": "integer", "description": "Grid row. Omit for auto-placement."},
                        "w": {"type": "integer", "description": "Width in columns. Omit for default."},
                        "h": {"type": "integer", "description": "Height in rows. Omit for default."},
                        "config": {"type": "object", "description": "Initial config for the widget. For text-block: {content: 'markdown text'}. For clock: {hour12: true}. For events: {daysAhead: 7}."},
                    },
                    "required": ["type"],
                },
            ),
            Tool(
                name="remove_widget",
                description="Remove a widget from the dashboard by its widget ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "widget_id": {"type": "string", "description": "Widget ID (required)"},
                        "tab_id": {"type": "string", "description": "Tab ID. Omit to search all tabs."},
                    },
                    "required": ["widget_id"],
                },
            ),
            Tool(
                name="create_tab",
                description="Create a new dashboard tab.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Tab name (required)"},
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="create_custom_widget",
                description="""Create a fully custom widget with HTML/CSS/JS. The widget renders in a sandboxed iframe with access to the Vault API. Use this to build ANY widget the user asks for: Pinterest boards, habit trackers, weather, countdown timers, shopping lists, embedded feeds, interactive checklists, data visualizations, etc.

The HTML has access to:
- vaultGet(path, params) — GET request to Vault API (e.g. vaultGet('/pessoal/tasks/'))
- vaultPost(path, data) — POST request to Vault API
- saveState(obj) / loadState(fallback) — persist widget-local state across reloads
- Base CSS with .card, .badge, .grid, .flex, .accent, .text-muted classes
- Full JS capabilities (fetch external APIs, DOM manipulation, timers, etc.)

Write clean, self-contained HTML. Include <style> for custom styles and <script> for interactivity.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Widget title shown in header (required)"},
                        "html": {"type": "string", "description": "HTML body content — can include <style> and <script> tags (required)"},
                        "tab_id": {"type": "string", "description": "Tab ID. Omit for first tab."},
                        "w": {"type": "integer", "description": "Width in grid columns (default 4)"},
                        "h": {"type": "integer", "description": "Height in grid rows (default 4)"},
                    },
                    "required": ["title", "html"],
                },
            ),
            Tool(
                name="set_dashboard",
                description="Replace the entire dashboard state. Use get_dashboard first to read current state, then modify and set. State shape: {tabs: [{id, name, widgets: [{id, type, x, y, w, h}]}], configs: {}}",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "state": {"type": "object", "description": "Full dashboard state object (required)"},
                    },
                    "required": ["state"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        try:
            result = await _execute_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]
        except Exception as e:
            error_text = str(e)
            if hasattr(e, 'response'):
                error_text = f"API {e.response.status_code}: {e.response.text[:500]}"
            return [TextContent(type="text", text=json.dumps({"error": error_text}, ensure_ascii=False))]

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

    if name == "update_spreadsheet":
        from tool_helpers import vault_put
        params = {"range": args["range"]}
        if args.get("account_email"):
            params["account_email"] = args["account_email"]
        client = get_client()
        resp = await client.put(
            f"{VAULT_API}/google/drive/sheets/{args['spreadsheet_id']}/",
            headers={"X-Profile-ID": pid, "Content-Type": "application/json"},
            params=params,
            json={"values": args["values"]},
        )
        resp.raise_for_status()
        return resp.json()

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

    # ── Financial Intelligence ──

    if name == "get_transactions":
        params = {"month_str": args["month_str"]}
        if args.get("search"):
            params["search"] = args["search"]
        if args.get("category"):
            params["category_name"] = args["category"]
        if args.get("account_id"):
            params["account"] = args["account_id"]
        params["limit"] = str(args.get("limit", 50))
        data = await vault_get("/transactions/", pid, params)
        results = data.get("results", data) if isinstance(data, dict) else data
        return [
            {
                "id": t.get("id"), "date": t.get("date"), "amount": t.get("amount"),
                "description": t.get("description"), "category": t.get("category_name"),
                "subcategory": t.get("subcategory_name"), "account": t.get("account_name"),
            }
            for t in (results if isinstance(results, list) else [])
        ]

    if name == "get_spending_trends":
        months = args.get("months", 3)
        return await vault_get("/analytics/trends/", pid, {"months": str(months)})

    if name == "get_projection":
        return await vault_get("/analytics/projection/", pid)

    if name == "get_recurring":
        params = {}
        if args.get("month_str"):
            params["month_str"] = args["month_str"]
        return await vault_get("/analytics/recurring/", pid, params)

    if name == "get_categories":
        return await vault_get("/categories/tree/", pid)

    if name == "get_accounts":
        data = await vault_get("/accounts/", pid)
        results = data.get("results", data) if isinstance(data, dict) else data
        return [{"id": a.get("id"), "name": a.get("name"), "type": a.get("type")} for a in (results if isinstance(results, list) else [])]

    # ── Dashboard / Widget Management ──

    # Widget defaults for auto-placement
    WIDGET_DEFAULTS = {
        "kpi-hoje": (3, 2), "kpi-atrasadas": (3, 2), "kpi-ativas": (3, 2), "kpi-projetos": (3, 2),
        "capture": (8, 1), "projects": (4, 1), "tasks": (4, 6), "reminders": (5, 6),
        "calendar": (6, 10), "events": (4, 5), "notes": (5, 5),
        "text-block": (4, 2), "clock": (2, 2), "greeting": (4, 1),
        "email-inbox": (4, 5), "drive-files": (4, 5),
        "fin-saldo": (3, 2), "fin-sobra": (3, 2), "fin-fatura": (3, 2),
        "custom": (4, 4),
    }

    if name == "get_dashboard":
        return await vault_get("/dashboard-state/", pid, {"profile_id": pid})

    if name == "add_widget":
        # Read current state
        current = await vault_get("/dashboard-state/", pid, {"profile_id": pid})
        state = current.get("state", {})
        tabs = state.get("tabs", [])
        if not tabs:
            tabs = [{"id": "default", "name": "Principal", "widgets": []}]

        tab_id = args.get("tab_id") or tabs[0]["id"]
        tab = next((t for t in tabs if t["id"] == tab_id), tabs[0])

        wtype = args["type"]
        dw, dh = WIDGET_DEFAULTS.get(wtype, (4, 4))
        w = args.get("w", dw)
        h = args.get("h", dh)

        # Auto-place if x/y not given
        if "x" in args and "y" in args:
            x, y = args["x"], args["y"]
        else:
            occupied = set()
            for wd in tab.get("widgets", []):
                for dy in range(wd.get("h", 1)):
                    for dx in range(wd.get("w", 1)):
                        occupied.add((wd.get("x", 0) + dx, wd.get("y", 0) + dy))
            x, y = 0, 0
            found = False
            for yy in range(100):
                for xx in range(13 - w):
                    if all((xx + dx, yy + dy) not in occupied for dy in range(h) for dx in range(w)):
                        x, y = xx, yy
                        found = True
                        break
                if found:
                    break

        import random, string
        wid = f"{wtype}-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        new_widget = {"id": wid, "type": wtype, "x": x, "y": y, "w": w, "h": h}

        tab["widgets"] = tab.get("widgets", []) + [new_widget]

        # Save widget config if provided
        configs = state.get("configs", {})
        if args.get("config"):
            configs[wid] = args["config"]
            state["configs"] = configs

        state["tabs"] = tabs
        from tool_helpers import vault_put
        await vault_put("/dashboard-state/", pid, {"state": state})
        return {"added": new_widget, "tab": tab_id}

    if name == "remove_widget":
        current = await vault_get("/dashboard-state/", pid, {"profile_id": pid})
        state = current.get("state", {})
        tabs = state.get("tabs", [])
        wid = args["widget_id"]
        removed = False
        for tab in tabs:
            before = len(tab.get("widgets", []))
            tab["widgets"] = [w for w in tab.get("widgets", []) if w["id"] != wid]
            if len(tab["widgets"]) < before:
                removed = True
                break
        if not removed:
            return {"error": f"Widget {wid} not found"}
        state["tabs"] = tabs
        from tool_helpers import vault_put
        await vault_put("/dashboard-state/", pid, {"state": state})
        return {"removed": wid}

    if name == "create_tab":
        current = await vault_get("/dashboard-state/", pid, {"profile_id": pid})
        state = current.get("state", {})
        tabs = state.get("tabs", [])
        import random, string
        tid = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        new_tab = {"id": tid, "name": args["name"], "widgets": []}
        tabs.append(new_tab)
        state["tabs"] = tabs
        from tool_helpers import vault_put
        await vault_put("/dashboard-state/", pid, {"state": state})
        return {"created": new_tab}

    if name == "create_custom_widget":
        # Read current state
        current = await vault_get("/dashboard-state/", pid, {"profile_id": pid})
        state = current.get("state", {})
        tabs = state.get("tabs", [])
        if not tabs:
            tabs = [{"id": "default", "name": "Principal", "widgets": []}]

        tab_id = args.get("tab_id") or tabs[0]["id"]
        tab = next((t for t in tabs if t["id"] == tab_id), tabs[0])

        w = args.get("w", 4)
        h = args.get("h", 4)

        # Auto-place
        occupied = set()
        for wd in tab.get("widgets", []):
            for dy in range(wd.get("h", 1)):
                for dx in range(wd.get("w", 1)):
                    occupied.add((wd.get("x", 0) + dx, wd.get("y", 0) + dy))
        x, y = 0, 0
        for yy in range(100):
            found = False
            for xx in range(13 - w):
                if all((xx + dx, yy + dy) not in occupied for dy in range(h) for dx in range(w)):
                    x, y = xx, yy
                    found = True
                    break
            if found:
                break

        import random, string
        wid = f"custom-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        new_widget = {"id": wid, "type": "custom", "x": x, "y": y, "w": w, "h": h}

        tab["widgets"] = tab.get("widgets", []) + [new_widget]
        configs = state.get("configs", {})
        configs[wid] = {"title": args["title"], "html": args["html"]}
        state["tabs"] = tabs
        state["configs"] = configs
        from tool_helpers import vault_put
        await vault_put("/dashboard-state/", pid, {"state": state})
        return {"created": wid, "title": args["title"], "tab": tab_id, "size": f"{w}x{h}"}

    if name == "set_dashboard":
        from tool_helpers import vault_put
        await vault_put("/dashboard-state/", pid, {"state": args["state"]})
        return {"ok": True}

    return {"error": f"Unknown tool: {name}"}
