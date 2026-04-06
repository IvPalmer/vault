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

from vault_tools import create_vault_mcp_server, set_profile

app = FastAPI(title="Vault Chat Sidecar")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "https://localhost:5175", "https://raphaels-mac-studio.tail5d4d09.ts.net:5175"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: profile_id -> session_id
_sessions: dict[str, str] = {}

# Conversation memory per profile (last N exchanges for context window)
_memory: dict[str, list[dict]] = {}
MAX_MEMORY = 20  # keep last 20 exchanges per profile

# Vault MCP tools server (in-process, no separate process needed)
_vault_mcp = create_vault_mcp_server()

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
    """Fetch lightweight context from Vault API (parallel).

    Since Claude now has MCP tools to fetch detailed data on demand,
    this context is kept minimal — just enough for awareness.
    """
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    headers = {"X-Profile-ID": profile_id}

    async def _get(path: str, params: dict | None = None) -> dict | list | None:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{VAULT_API}/api{path}", headers=headers, params=params or {})
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass
        return None

    # Fetch all in parallel
    tasks_p, projects_p, accounts_p = await asyncio.gather(
        _get("/pessoal/tasks/"),
        _get("/pessoal/projects/"),
        _get("/google/accounts/"),
    )

    parts: list[str] = []

    # Tasks — just counts
    if tasks_p:
        tasks = tasks_p.get("results", tasks_p) if isinstance(tasks_p, dict) else tasks_p
        active = [t for t in tasks if t.get("status") != "done"]
        overdue = [t for t in active if t.get("due_date") and t["due_date"] < today_str]
        due_today = [t for t in active if t.get("due_date") == today_str]
        parts.append(f"Tarefas: {len(active)} ativas, {len(due_today)} hoje, {len(overdue)} atrasadas")

    # Projects — just names
    if projects_p:
        projects = projects_p.get("results", projects_p) if isinstance(projects_p, dict) else projects_p
        active_p = [p["name"] for p in projects if p.get("status") == "active"]
        if active_p:
            parts.append(f"Projetos: {', '.join(active_p)}")

    # Google accounts — just list emails
    if accounts_p:
        accts = accounts_p if isinstance(accounts_p, list) else accounts_p.get("accounts", [])
        emails = [a.get("email", a) if isinstance(a, dict) else str(a) for a in accts]
        if emails:
            parts.append(f"Contas Google: {', '.join(emails)}")

    return "\n".join(parts) if parts else ""


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

    return f"""Voce e a assistente pessoal de {profile_name} no Vault, um app de organizacao pessoal e financas.

QUEM VOCE ESTA FALANDO:
{who}

PERSONALIDADE:
{personality}
Seja concisa, direta e calorosa. Use markdown quando ajudar (negrito, listas).
Responda SEMPRE em portugues brasileiro.

VOCE E UMA ASSISTENTE PESSOAL COMPLETA — nao apenas um chatbot.
Voce pode pesquisar na internet, ler paginas web, consultar e modificar dados do Vault,
criar widgets personalizados, editar planilhas, enviar emails, e muito mais.
USE AS FERRAMENTAS para buscar informacoes antes de responder — nunca invente dados.

PESQUISA E WEB:
- WebSearch: pesquisar qualquer coisa na internet (receitas, noticias, precos, tutoriais, etc.)
- WebFetch: ler o conteudo de uma pagina web (artigos, documentacao, etc.)

ORGANIZACAO PESSOAL:
- Tarefas: list_tasks, create_task, update_task, delete_task
- Notas: list_notes, create_note, delete_note
- Projetos: list_projects, create_project
- Lembretes Apple: get_reminder_lists, get_reminders, add_reminder, complete_reminder
- Calendario: get_calendar_events, create_calendar_event

GOOGLE (email, drive, docs, sheets):
- search_emails, read_email, send_email, draft_email, trash_email
- search_drive, read_document, read_spreadsheet, update_spreadsheet
- Pode ler um doc, cruzar com dados do Vault, e escrever resultado em uma planilha

FINANCAS (dados reais do banco):
- get_finances: resumo do mes (saldo, renda, gastos, fatura CC, poupanca)
- get_transactions: buscar transacoes por mes, categoria, descricao, conta
- get_spending_trends: tendencias de gasto por categoria ao longo de meses
- get_projection: projecao financeira futura (saldo, renda, gastos por mes)
- get_recurring: despesas fixas, investimentos, cartao — esperado vs real
- get_categories, get_accounts: listar categorias e contas
- categorize_transaction: recategorizar uma transacao

DASHBOARD (configurar a pagina da usuaria):
- get_dashboard, add_widget, remove_widget, create_tab, set_dashboard
- Widgets built-in: kpi-hoje, kpi-atrasadas, kpi-ativas, kpi-projetos,
  capture, projects, tasks, reminders, calendar, events, notes, text-block,
  clock, greeting, email-inbox, drive-files, fin-saldo, fin-sobra, fin-fatura

WIDGETS PERSONALIZADOS (seu superpoder!):
- create_custom_widget: cria qualquer widget com HTML/CSS/JS completo
- O widget roda em iframe com acesso a API do Vault (vaultGet, vaultPost)
- Pode persistir estado local (saveState/loadState)
- Exemplos do que voce pode criar:
  * Lista de compras interativa com checkboxes que salvam estado
  * Board de Pinterest com imagens de uma URL
  * Tracker de habitos com calendario visual
  * Countdown para um evento
  * Painel do clima buscando API externa
  * Checklist de limpeza semanal com progresso
  * Galeria de fotos, player de musica, feed RSS
  * Qualquer coisa que a usuaria imaginar!
- Grade de 12 colunas. A usuaria precisa recarregar apos mudancas no dashboard.

CAPACIDADES EXTRAS:
- Bash: executar comandos no terminal (curl, python, jq, etc.) para processar dados
- Read/Grep/Glob: ler e buscar em arquivos locais
- Pode combinar ferramentas: pesquisar na web + criar widget, ler planilha + analisar + responder

REGRAS IMPORTANTES:
1. ACOES DESTRUTIVAS (send_email, delete_task, delete_note, trash_email):
   SEMPRE pergunte "Confirma?" e espere a usuaria responder "sim" antes de executar.
2. NUNCA execute rm, git push, docker, ou qualquer comando destrutivo no Bash.
   Bash e para LEITURA e processamento de dados apenas (curl, python, jq, cat, etc.)
3. NUNCA modifique codigo fonte do app (arquivos .py, .jsx, .css, .js).
4. Use as ferramentas para buscar dados atualizados — o contexto abaixo pode estar desatualizado.
5. Para emails: a usuaria tem multiplas contas Google. Pergunte de qual conta
   enviar/buscar quando nao estiver claro pelo contexto.

DATA ATUAL: {datetime.now().strftime('%A, %d de %B de %Y')}

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

    # Set active profile for MCP tools
    set_profile(req.profile_id)

    _ALLOWED_TOOLS = [
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
        "mcp__vault-tools__update_spreadsheet",
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
        "mcp__vault-tools__get_transactions",
        "mcp__vault-tools__get_spending_trends",
        "mcp__vault-tools__get_projection",
        "mcp__vault-tools__get_recurring",
        "mcp__vault-tools__get_categories",
        "mcp__vault-tools__get_accounts",
        "mcp__vault-tools__get_dashboard",
        "mcp__vault-tools__add_widget",
        "mcp__vault-tools__remove_widget",
        "mcp__vault-tools__create_tab",
        "mcp__vault-tools__create_custom_widget",
        "mcp__vault-tools__set_dashboard",
    ]

    options = ClaudeAgentOptions(
        max_turns=12,
        model="claude-sonnet-4-6",
        cwd="/Users/palmer/Work/Dev/Vault",
        system_prompt=system_prompt,
        include_partial_messages=True,
        mcp_servers={"vault-tools": {"type": "sdk", "name": "vault-tools", "instance": _vault_mcp}},
        permission_mode="bypassPermissions",
        allowed_tools=[
            *_ALLOWED_TOOLS,
            # Claude built-in tools
            "WebSearch",
            "WebFetch",
            "Bash",
            "Read",
            "Grep",
            "Glob",
        ],
        disallowed_tools=[
            # Block only destructive/code-editing tools
            "Edit",       # don't modify source code
            "Write",      # don't create files on disk
            "NotebookEdit",
            "Agent",      # don't spawn sub-agents
        ],
    )

    # Resume existing session if available
    existing_session = _sessions.get(req.profile_id)
    if existing_session:
        options.resume = existing_session

    full_response = ""
    last_sent_len = 0

    try:
        client = ClaudeSDKClient(options)
        await client.connect()
        await client.query(prompt)

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
                    if text and len(text) > last_sent_len:
                        # Stream incremental text
                        full_response = text
                        yield f"data: {json.dumps({'content': text}, ensure_ascii=False)}\n\n"
                        last_sent_len = len(text)

            elif isinstance(message, ResultMessage):
                session_id = getattr(message, "session_id", None)
                # Send final text if we haven't yet
                result_text = getattr(message, "text", None)
                if result_text and result_text != full_response:
                    full_response = result_text
                    yield f"data: {json.dumps({'content': result_text}, ensure_ascii=False)}\n\n"
                break

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
