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

from sandbox import needs_sandbox, ensure_worktree, validate, merge_back, discard
from memory_store import get_context_for_prompt, save_conversation_summary
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
MAX_MEMORY = 50  # keep last 50 exchanges per profile

# Vault MCP tools server (in-process, no separate process needed)
_vault_mcp = create_vault_mcp_server()

VAULT_API = os.environ.get("VAULT_API", "http://localhost:8001")
_VAULT_API_HOST = os.environ.get("VAULT_API_HOST")

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
    if _VAULT_API_HOST:
        headers["Host"] = _VAULT_API_HOST

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
    tasks_p, projects_p, accounts_p, exams_p, pregnancies_p = await asyncio.gather(
        _get("/pessoal/tasks/"),
        _get("/pessoal/projects/"),
        _get("/google/accounts/"),
        _get("/saude/exams/"),
        _get("/saude/pregnancies/"),
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

    # Saúde — exam counts, recent exam list, pregnancy summary
    if exams_p:
        exams = exams_p.get("results", exams_p) if isinstance(exams_p, dict) else exams_p
        if exams:
            recent = exams[:5]
            recent_lines = [f"  - {e.get('data', '?')}: {e.get('nome', e.get('tipo', '?'))}" for e in recent]
            parts.append(f"Saude: {len(exams)} exames registrados. Recentes:\n" + "\n".join(recent_lines))

    if pregnancies_p:
        pregs = pregnancies_p.get("results", pregnancies_p) if isinstance(pregnancies_p, dict) else pregnancies_p
        ativas = [p for p in pregs if p.get("status") == "ativa"]
        for p in ativas:
            dpp = p.get("dpp")
            dum = p.get("dum")
            ig_str = ""
            if dum:
                try:
                    dum_dt = datetime.strptime(dum, "%Y-%m-%d")
                    days = (now - dum_dt).days
                    if 0 <= days <= 320:
                        weeks, rem = divmod(days, 7)
                        ig_str = f", IG atual: {weeks}+{rem}"
                except Exception:
                    pass
            parts.append(f"Gestacao ativa (DUM {dum}, DPP {dpp}{ig_str})")

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
        recent = memory[-10:]  # last 5 exchanges
        mem_lines = []
        for m in recent:
            role = "User" if m["role"] == "user" else "Assistant"
            content = m["content"][:500]
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

SAUDE (exames, sinais vitais, gestacao):
- get_health_exams: lista todos os exames (hemograma, USG, TOTG, urina, sangue, imagem)
  Filtra por tipo, data, limit. Use SEMPRE para responder perguntas sobre exames.
- get_health_exam: detalhe completo de um exame (todos os valores)
- get_vitals: leituras de PA, peso, glicemia, FC ao longo do tempo
- get_pregnancies: gestacoes (ativa/finalizada/perda) com DUM, DPP, plano, carencia
- get_prenatal_consultations: consultas pre-natais com PA, peso, FCF, IG, conduta
- add_health_exam: criar novo registro de exame com valores normalizados
- add_vital_reading: registrar PA, peso, glicemia, etc
- Cruze dados: ex: comparar hemograma atual vs anterior, evolucao de peso na gestacao

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

MEMORIA PERSISTENTE:
- Voce tem memoria persistente entre conversas via save_memory/recall_memory
- SALVE PROATIVAMENTE informacoes importantes: preferencias, decisoes, nomes de pessoas,
  datas importantes, contexto de projetos, habitos, qualquer coisa util para o futuro
- No inicio de cada conversa, suas memorias salvas aparecem no contexto automaticamente
- Use recall_memory para buscar algo especifico de conversas passadas
- Exemplos do que salvar: "Palmer prefere ver gastos por categoria", "Rafa tem reuniao
  toda terca as 10h", "Decidiram trocar de plano de saude em junho"

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
        "content": content[:2000],  # truncate for memory efficiency
        "ts": datetime.now().isoformat(),
    })
    # Trim to MAX_MEMORY
    if len(_memory[profile_id]) > MAX_MEMORY:
        _memory[profile_id] = _memory[profile_id][-MAX_MEMORY:]


async def _stream_chat(req: ChatRequest):
    """Generator that yields SSE events from Claude."""
    context = await _fetch_context(req.profile_id)
    persistent_memory = get_context_for_prompt(req.profile_id)
    if persistent_memory:
        context = context + "\n\n" + persistent_memory if context else persistent_memory
    system_prompt = _build_system_prompt(req.profile_id, req.profile_name, context)

    # Record user message in memory
    _record_memory(req.profile_id, "user", req.message)

    # Build the prompt with attachment info if present
    prompt = req.message
    if req.attachment_name and req.attachment_data:
        att_type = req.attachment_type or "unknown"
        if att_type.startswith("text/"):
            # Text files: inline the content
            try:
                decoded = base64.b64decode(req.attachment_data).decode("utf-8", errors="replace")
                prompt += f"\n\n[Arquivo anexado: {req.attachment_name}]\n```\n{decoded[:5000]}\n```"
            except Exception:
                prompt += f"\n\n[Arquivo anexado: {req.attachment_name} ({att_type}) — falha ao decodificar]"
        else:
            # Binary files (images, PDFs, etc.): save to temp and let agent Read it
            try:
                import tempfile
                suffix = Path(req.attachment_name).suffix or ".bin"
                tmp = Path(tempfile.mkdtemp(prefix="vault-attach-")) / f"attachment{suffix}"
                tmp.write_bytes(base64.b64decode(req.attachment_data))
                prompt += f"\n\n[Arquivo anexado: {req.attachment_name} ({att_type})]\nSalvo em: {tmp}\nUse a ferramenta Read para visualizar o arquivo."
            except Exception:
                prompt += f"\n\n[Arquivo anexado: {req.attachment_name} ({att_type}) — falha ao salvar]"

    # Set active profile for MCP tools
    set_profile(req.profile_id)

    # ── Sandbox decision ──
    use_sandbox = await needs_sandbox(req.message)
    worktree_path = None
    agent_cwd = os.environ.get("AGENT_CWD", "/Users/palmer/Work/Dev/vault")
    if not os.path.isdir(agent_cwd):
        agent_cwd = "/tmp"

    if use_sandbox:
        yield f"data: {json.dumps({'sandbox_status': 'preparing', 'message': 'Preparando ambiente isolado...'})}\n\n"
        try:
            worktree_path = await ensure_worktree()
            agent_cwd = str(worktree_path)
            yield f"data: {json.dumps({'sandbox_status': 'ready', 'message': 'Sandbox pronto. Editando em ambiente isolado.'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'sandbox_status': 'error', 'message': f'Falha ao criar sandbox: {exc}'})}\n\n"
            use_sandbox = False
            worktree_path = None

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
        "mcp__vault-tools__save_memory",
        "mcp__vault-tools__recall_memory",
        "mcp__vault-tools__delete_memory",
    ]

    # Build tool lists based on sandbox mode
    allowed = [
        *_ALLOWED_TOOLS,
        "WebSearch",
        "WebFetch",
        "Bash",
        "Read",
        "Grep",
        "Glob",
    ]
    disallowed = [
        "NotebookEdit",
    ]

    if use_sandbox:
        # In sandbox mode, allow Edit/Write/Agent for code changes
        allowed.extend(["Edit", "Write", "Agent"])
        system_prompt += """

MODO SANDBOX ATIVO:
Voce esta trabalhando em um ambiente isolado (worktree git).
Pode usar Edit, Write, Bash e Agent livremente para modificar arquivos.
Suas alteracoes serao validadas (vite build) antes de serem aplicadas ao app.
Se o build falhar, voce tera chance de corrigir (ate 3 tentativas).

ARQUITETURA DO VAULT (frontend):

Diretorio: src/components/
Tech: React + Vite, CSS Modules (.module.css), GridStack dashboard

COMPONENTES PRINCIPAIS:
- PersonalOrganizer.jsx (2358 linhas) — MEGA COMPONENTE, contem:
  * KpiCard (linha ~104) — cards de contagem (tarefas hoje, atrasadas, etc.)
  * QuickCapture (~115) — barra de captura rapida de tarefas/notas
  * ProjectsBar (~241) — barra de projetos com filtro
  * TaskList (~338) — lista de tarefas com kanban, drag-drop, prioridades
  * NotesList (~795) — lista de notas com editor
  * UpcomingEvents (~943) — lista de proximos eventos
  * PersonalCalendar (~1098) — calendario completo (month/week/day views)
    - Week view: grade horaria 6h-23h com eventos posicionados
    - Day view: grade horaria single-column
    - Month view: grid de dias com eventos
    - Usa HOURS, WEEKDAYS, buildCalendarDays(), getWeekDays()
  * PersonalReminders (~1519) — lembretes Apple com listas
  * TabBar (~1699) — abas do dashboard
  * WidgetCatalog (~1849) — catalogo de widgets pra adicionar
  * PersonalOrganizer (~1896) — componente principal com auth
  * PersonalOrganizerInner (~1906) — grid de widgets, layout persistente
  * DashboardGrid (~2197) — grid GridStack
- PersonalOrganizer.module.css — TODOS os estilos do modulo Pessoal

WIDGETS (src/components/widgets/):
- ChatWidget.jsx (510 linhas) — chat com sidecar, SSE streaming
- EmailWidget.jsx (259) — inbox Gmail
- DriveWidget.jsx (237) — arquivos Google Drive
- FinanceWidgets.jsx — KPIs financeiros (saldo, sobra, fatura)
- ClockWidget.jsx — relogio digital
- GreetingWidget.jsx — saudacao com hora do dia
- TextBlock.jsx — bloco de texto editavel
- CustomWidget.jsx (186) — iframe pra widgets custom (HTML/CSS/JS)
- WidgetRegistry.js — metadata de todos os widgets (tamanhos, categorias)
- WidgetSettingsPanel.jsx — painel de config compartilhado

MODULO FINANCEIRO (src/components/):
- Home.jsx (791) — pagina principal financeira
- MetricasSection.jsx (1043) — metricas do mes
- CardsSection.jsx (379) — faturas de cartao
- CartaoSection.jsx (159) — secao cartao no controle
- CheckingSection.jsx (179) — conta corrente
- InvestmentSection.jsx (320) — investimentos
- RecurringSection.jsx (524) — despesas fixas
- ProjectionSection.jsx (301) — projecao futura
- OrcamentoSection.jsx (171) — orcamento mensal
- Analytics.jsx (183) — graficos/charts
- Settings.jsx (1810) — configuracoes
- VaultTable.jsx (195) — tabela reutilizavel

PADROES IMPORTANTES:
- CSS Modules: import styles from './Component.module.css'
- API: useQuery do react-query, fetch com X-Profile-ID header
- Estado do dashboard: useDashboardState hook, salva no backend
- Widgets recebem { config, onConfigChange } como props
- Novos widgets: criar arquivo + registrar em WidgetRegistry.js + PersonalOrganizer.jsx
- Template literals: usar backticks normais ` NAO escapar com backslash
- Componentes no PersonalOrganizer.jsx sao funcoes internas (nao exportadas)
- Variaveis devem ser definidas no MESMO componente onde sao usadas"""
    else:
        # Normal mode: block code-editing tools and sub-agents
        disallowed.extend(["Edit", "Write", "Agent"])
        system_prompt += """

RESTRICAO BASH ESTRITA:
Bash e SOMENTE para leitura e processamento de dados. PROIBIDO:
- cat > arquivo, echo > arquivo, tee, sed -i, awk (escrita)
- Qualquer comando que CRIE ou MODIFIQUE arquivos no disco
- mv, cp, rm de arquivos do projeto
Se a tarefa requer editar codigo, diga ao usuario para pedir pelo Claude Code (terminal)."""

    options = ClaudeAgentOptions(
        max_turns=100 if use_sandbox else 50,
        model="claude-opus-4-6",
        cwd=agent_cwd,
        system_prompt=system_prompt,
        include_partial_messages=True,
        mcp_servers={"vault-tools": {"type": "sdk", "name": "vault-tools", "instance": _vault_mcp}},
        permission_mode="bypassPermissions",
        allowed_tools=allowed,
        disallowed_tools=disallowed,
    )

    # Resume existing session if available (not in sandbox — those are one-shot)
    if not use_sandbox:
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

        if session_id and not use_sandbox:
            _sessions[req.profile_id] = session_id

        await client.disconnect()

    except Exception as exc:
        error_msg = str(exc)
        full_response = f"Erro: {error_msg}"
        yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"

    # ── Sandbox: validate and merge (with retry) ──
    if use_sandbox and worktree_path:
        MAX_BUILD_RETRIES = 3
        build_ok = False

        for attempt in range(1, MAX_BUILD_RETRIES + 1):
            yield f"data: {json.dumps({'sandbox_status': 'validating', 'message': f'Validando build... (tentativa {attempt}/{MAX_BUILD_RETRIES})'})}\n\n"

            ok, build_output = await validate(worktree_path)
            if ok:
                build_ok = True
                merged = await merge_back(worktree_path)
                if merged:
                    file_list = ", ".join(merged[:5])
                    if len(merged) > 5:
                        file_list += f" (+{len(merged) - 5})"
                    yield f"data: {json.dumps({'sandbox_status': 'merged', 'message': f'Build OK! Arquivos atualizados: {file_list}'})}\n\n"
                else:
                    yield f"data: {json.dumps({'sandbox_status': 'no_changes', 'message': 'Nenhum arquivo modificado.'})}\n\n"
                break
            else:
                error_lines = build_output.strip().split("\n")[-8:]
                error_summary = "\n".join(error_lines)

                if attempt < MAX_BUILD_RETRIES:
                    # Ask the agent to fix the build error
                    yield f"data: {json.dumps({'sandbox_status': 'fixing', 'message': f'Build falhou. Corrigindo... ({attempt}/{MAX_BUILD_RETRIES})'})}\n\n"
                    fix_prompt = f"O vite build falhou com o seguinte erro:\n\n```\n{error_summary}\n```\n\nCorrija o erro nos arquivos que voce editou. Use Edit ou Write para consertar."
                    try:
                        fix_options = ClaudeAgentOptions(
                            max_turns=20,
                            model="claude-opus-4-6",
                            cwd=str(worktree_path),
                            system_prompt="Voce e um assistente de desenvolvimento. Corrija o erro de build. Seja preciso e direto.",
                            mcp_servers={"vault-tools": {"type": "sdk", "name": "vault-tools", "instance": _vault_mcp}},
                            permission_mode="bypassPermissions",
                            allowed_tools=["Edit", "Write", "Read", "Grep", "Glob", "Bash"],
                            disallowed_tools=["NotebookEdit"],
                        )
                        fix_client = ClaudeSDKClient(fix_options)
                        await fix_client.connect()
                        await fix_client.query(fix_prompt)
                        async for raw_data in fix_client._query.receive_messages():
                            try:
                                msg = parse_message(raw_data)
                            except Exception:
                                continue
                            if isinstance(msg, ResultMessage):
                                break
                        await fix_client.disconnect()
                    except Exception:
                        pass  # If fix agent fails, next iteration will catch it
                else:
                    # Final attempt failed — discard
                    await discard(worktree_path)
                    yield f"data: {json.dumps({'sandbox_status': 'failed', 'message': 'Build falhou apos 3 tentativas — alteracoes descartadas.', 'error': error_summary})}\n\n"

    # Record assistant response in memory
    if full_response:
        _record_memory(req.profile_id, "assistant", full_response)

    # Auto-summarize conversation for persistent memory
    if full_response and len(full_response) > 50:
        try:
            user_msg = req.message[:200]
            bot_msg = full_response[:300]
            summary = f"User: {user_msg} | Bot: {bot_msg}"
            save_conversation_summary(req.profile_id, summary)
        except Exception:
            pass

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
