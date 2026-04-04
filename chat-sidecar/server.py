"""
Chat Sidecar — FastAPI server that proxies chat to Claude
via claude_agent_sdk (uses local Claude Code CLI auth, no API key needed).

Features:
- Per-profile sessions with memory/context continuity
- Full Vault context (tasks, notes, events, calendar, metricas)
- File/image attachment support (base64)
- Profile-aware system prompt (knows Palmer vs Rafa)
"""

import asyncio
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
)
from claude_agent_sdk._errors import MessageParseError
from claude_agent_sdk._internal.message_parser import parse_message

app = FastAPI(title="Vault Chat Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: profile_id -> session_id
_sessions: dict[str, str] = {}

# Conversation memory per profile (last N exchanges for context window)
_memory: dict[str, list[dict]] = {}
MAX_MEMORY = 20  # keep last 20 exchanges per profile

VAULT_API = "http://localhost:8001"

# Profile metadata for personalized responses
PROFILE_META = {
    "a29184ea-9d4d-4c65-8300-386ed5b07fca": {
        "name": "Palmer",
        "lang_hint": "Palmer speaks both English and Portuguese. Default to Portuguese unless he writes in English.",
        "context": "Palmer is the developer and primary user. He manages household finances, works as a freelance software engineer (paid in USD via Wise), and is technical.",
    },
}
RAFA_HINT = (
    "Rafaella (Rafa) is Palmer's partner. She is not technical. "
    "Be warm, friendly, and explain things simply. "
    "Always respond in Portuguese. Use informal language (voce, not o senhor)."
)


class ChatRequest(BaseModel):
    message: str
    profile_id: str
    profile_name: str = "User"
    attachment_name: Optional[str] = None
    attachment_data: Optional[str] = None  # base64-encoded
    attachment_type: Optional[str] = None  # mime type


async def _fetch_context(profile_id: str) -> str:
    """Fetch comprehensive context from Vault API."""
    now = datetime.now()
    month_str = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")
    headers = {"X-Profile-ID": profile_id}
    parts: list[str] = []

    async with httpx.AsyncClient(timeout=5.0) as client:
        # Tasks
        try:
            resp = await client.get(f"{VAULT_API}/api/pessoal/tasks/", headers=headers)
            if resp.status_code == 200:
                tasks = resp.json()
                if isinstance(tasks, dict):
                    tasks = tasks.get("results", tasks.get("data", []))
                active = [t for t in tasks if t.get("status") != "done"]
                overdue = [t for t in active if t.get("due_date") and t["due_date"] < today_str]
                due_today = [t for t in active if t.get("due_date") == today_str]
                doing = [t for t in active if t.get("status") == "doing"]
                upcoming = [t for t in active if t.get("due_date") and t["due_date"] > today_str][:5]

                if overdue:
                    lines = [f"  - {t['title']} (vencida {t['due_date']})" for t in overdue[:5]]
                    parts.append("TAREFAS ATRASADAS:\n" + "\n".join(lines))
                if due_today:
                    lines = [f"  - {t['title']}" for t in due_today]
                    parts.append("TAREFAS PARA HOJE:\n" + "\n".join(lines))
                if doing:
                    lines = [f"  - {t['title']}" for t in doing[:5]]
                    parts.append("EM ANDAMENTO:\n" + "\n".join(lines))
                if upcoming:
                    lines = [f"  - {t['title']} ({t['due_date']})" for t in upcoming]
                    parts.append("PROXIMAS:\n" + "\n".join(lines))
                if not overdue and not due_today and not doing:
                    parts.append("Nenhuma tarefa pendente para hoje.")
                parts.append(f"Total tarefas ativas: {len(active)}")
        except Exception:
            pass

        # Notes (recent)
        try:
            resp = await client.get(f"{VAULT_API}/api/pessoal/notes/", headers=headers)
            if resp.status_code == 200:
                notes = resp.json()
                if isinstance(notes, dict):
                    notes = notes.get("results", notes.get("data", []))
                if notes:
                    recent = sorted(notes, key=lambda n: n.get("updated_at", ""), reverse=True)[:5]
                    lines = []
                    for n in recent:
                        title = n.get("title") or "(sem titulo)"
                        content = (n.get("content") or "")[:100]
                        lines.append(f"  - {title}: {content}")
                    parts.append("NOTAS RECENTES:\n" + "\n".join(lines))
        except Exception:
            pass

        # Projects
        try:
            resp = await client.get(f"{VAULT_API}/api/pessoal/projects/", headers=headers)
            if resp.status_code == 200:
                projects = resp.json()
                if isinstance(projects, dict):
                    projects = projects.get("results", projects.get("data", []))
                active_projects = [p for p in projects if p.get("status") == "active"]
                if active_projects:
                    lines = [f"  - {p['name']} ({p.get('task_count', 0)} tarefas)" for p in active_projects]
                    parts.append("PROJETOS ATIVOS:\n" + "\n".join(lines))
        except Exception:
            pass

        # Metricas (financial summary)
        try:
            resp = await client.get(
                f"{VAULT_API}/api/analytics/metricas/",
                headers=headers,
                params={"month_str": month_str},
            )
            if resp.status_code == 200:
                m = resp.json()
                lines = []
                for key, label in [
                    ("saldo_projetado", "Saldo projetado"),
                    ("orcamento_variavel", "Orcamento variavel"),
                    ("variable_spending", "Gastos variaveis"),
                    ("fatura_total", "Fatura CC"),
                    ("income_total", "Renda"),
                ]:
                    val = m.get(key)
                    if val is not None:
                        lines.append(f"  {label}: R$ {val:,.2f}")
                if lines:
                    parts.append(f"FINANCEIRO ({month_str}):\n" + "\n".join(lines))
        except Exception:
            pass

        # Calendar events (next 14 days)
        try:
            time_min = now.strftime("%Y-%m-%dT00:00:00Z")
            from datetime import timedelta
            time_max = (now + timedelta(days=14)).strftime("%Y-%m-%dT23:59:59Z")
            resp = await client.get(
                f"{VAULT_API}/api/calendar/events/",
                headers=headers,
                params={"context": "personal", "time_min": time_min, "time_max": time_max},
            )
            if resp.status_code == 200:
                cal_data = resp.json()
                events = cal_data.get("events", [])
                if events:
                    lines = []
                    for e in events[:12]:
                        title = e.get("title") or e.get("summary") or "?"
                        start_raw = e.get("start", "")
                        # start can be a string (date or datetime) or dict
                        if isinstance(start_raw, dict):
                            start_str = start_raw.get("dateTime", start_raw.get("date", "?"))
                        else:
                            start_str = str(start_raw)
                        # Format datetime nicely
                        if "T" in start_str:
                            start_str = start_str[:16].replace("T", " ")
                        all_day = e.get("all_day", False)
                        loc = e.get("location", "")
                        loc_str = f" @ {loc.split(chr(10))[0]}" if loc else ""
                        day_str = " (dia todo)" if all_day else ""
                        lines.append(f"  - {title} ({start_str}{day_str}{loc_str})")
                    parts.append("CALENDARIO/PROXIMOS EVENTOS:\n" + "\n".join(lines))
        except Exception:
            pass

    return "\n\n".join(parts) if parts else "Nenhum dado disponivel no momento."


def _build_system_prompt(profile_id: str, profile_name: str, context: str) -> str:
    """Build a rich system prompt with profile awareness and context."""
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
        memory_section = "\n\nRECENT CONVERSATION:\n" + "\n".join(mem_lines)

    return f"""You are a personal assistant embedded inside Vault, a personal finance and daily organizer app.

WHO YOU'RE TALKING TO:
{who}

PERSONALITY:
{personality}
Be concise but warm. Use markdown formatting (bold, lists) when helpful.
When asked about tasks, finances, or schedule, use the context below to give accurate answers.
If asked to do something (create task, draft document, etc.), help directly.
If you don't have enough information, say so honestly.

CURRENT DATE: {datetime.now().strftime('%A, %d de %B de %Y')}

{context}{memory_section}"""


def _record_memory(profile_id: str, role: str, content: str):
    """Record a message in per-profile conversation memory."""
    if profile_id not in _memory:
        _memory[profile_id] = []
    _memory[profile_id].append({
        "role": role,
        "content": content[:500],  # truncate for memory efficiency
        "ts": datetime.now().isoformat(),
    })
    # Trim to MAX_MEMORY
    if len(_memory[profile_id]) > MAX_MEMORY:
        _memory[profile_id] = _memory[profile_id][-MAX_MEMORY:]


async def _stream_chat(req: ChatRequest):
    """Generator that yields SSE events from Claude."""
    context = await _fetch_context(req.profile_id)
    system_prompt = _build_system_prompt(req.profile_id, req.profile_name, context)

    # Record user message in memory
    _record_memory(req.profile_id, "user", req.message)

    # Build the prompt with attachment info if present
    prompt = req.message
    if req.attachment_name:
        prompt += f"\n\n[Arquivo anexado: {req.attachment_name} ({req.attachment_type or 'unknown'})]"
        if req.attachment_data and req.attachment_type and req.attachment_type.startswith("text/"):
            try:
                decoded = base64.b64decode(req.attachment_data).decode("utf-8", errors="replace")
                prompt += f"\n\nConteudo do arquivo:\n```\n{decoded[:5000]}\n```"
            except Exception:
                pass

    options = ClaudeAgentOptions(
        max_turns=10,
        cwd="/Users/palmer/Work/Dev/Vault",
        system_prompt=system_prompt,
        include_partial_messages=False,
    )

    # Resume existing session if available
    existing_session = _sessions.get(req.profile_id)
    if existing_session:
        options.resume = existing_session

    full_response = ""
    response_sent = False

    try:
        client = ClaudeSDKClient(options)
        await client.connect()
        await client.query(prompt)

        # Collect all messages, extract text from the last AssistantMessage only
        last_assistant_text = ""
        session_id = None

        async for raw_data in client._query.receive_messages():
            try:
                message = parse_message(raw_data)
            except (MessageParseError, Exception):
                continue

            if isinstance(message, AssistantMessage):
                content_blocks = getattr(message, "content", [])
                if isinstance(content_blocks, list):
                    text = ""
                    for block in content_blocks:
                        if hasattr(block, "text") and block.text:
                            text += block.text
                    if text:
                        last_assistant_text = text

            elif isinstance(message, ResultMessage):
                session_id = getattr(message, "session_id", None)
                break

        # Send the final response once
        if last_assistant_text:
            full_response = last_assistant_text
            yield f"data: {json.dumps({'content': last_assistant_text}, ensure_ascii=False)}\n\n"

        if session_id:
            _sessions[req.profile_id] = session_id

        await client.disconnect()

    except Exception as exc:
        error_msg = str(exc)
        full_response = f"Erro: {error_msg}"
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

    # Record assistant response in memory
    if full_response:
        _record_memory(req.profile_id, "assistant", full_response)

    yield f"data: {json.dumps({'done': True})}\n\n"


@app.post("/chat")
async def chat(req: ChatRequest):
    return StreamingResponse(
        _stream_chat(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/clear")
async def clear_session(profile_id: str = ""):
    """Clear session and memory for a profile."""
    if profile_id in _sessions:
        del _sessions[profile_id]
    if profile_id in _memory:
        del _memory[profile_id]
    return {"status": "cleared"}


@app.get("/health")
async def health():
    return {"status": "ok", "sessions": len(_sessions)}
