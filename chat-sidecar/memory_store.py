"""
Persistent memory for the chat sidecar.

Two types of memory per profile:
- facts: key information extracted by the bot (preferences, decisions, context)
- conversations: summaries of past conversations (auto-generated)

Stored as JSON files in chat-sidecar/memory/{profile_id}.json
"""
import json
from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

MAX_FACTS = 100
MAX_CONVERSATIONS = 50


def _memory_path(profile_id: str) -> Path:
    return MEMORY_DIR / f"{profile_id}.json"


def _load(profile_id: str) -> dict:
    path = _memory_path(profile_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"facts": [], "conversations": []}


def _save(profile_id: str, data: dict):
    path = _memory_path(profile_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def save_fact(profile_id: str, fact: str, category: str = "geral") -> str:
    """Save a fact/preference/decision to persistent memory."""
    data = _load(profile_id)
    # Check for duplicates (same content)
    for existing in data["facts"]:
        if existing["content"].lower().strip() == fact.lower().strip():
            return "Fato ja existe na memoria."
    data["facts"].append({
        "content": fact,
        "category": category,
        "ts": datetime.now().isoformat(),
    })
    # Trim oldest if over limit
    if len(data["facts"]) > MAX_FACTS:
        data["facts"] = data["facts"][-MAX_FACTS:]
    _save(profile_id, data)
    return "Fato salvo na memoria."


def delete_fact(profile_id: str, fact_index: int) -> str:
    """Delete a fact by index (0-based)."""
    data = _load(profile_id)
    if 0 <= fact_index < len(data["facts"]):
        removed = data["facts"].pop(fact_index)
        _save(profile_id, data)
        return f"Removido: {removed['content']}"
    return "Indice invalido."


def save_conversation_summary(profile_id: str, summary: str):
    """Save a conversation summary (called automatically after each session)."""
    data = _load(profile_id)
    data["conversations"].append({
        "summary": summary,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "ts": datetime.now().isoformat(),
    })
    if len(data["conversations"]) > MAX_CONVERSATIONS:
        data["conversations"] = data["conversations"][-MAX_CONVERSATIONS:]
    _save(profile_id, data)


def recall(profile_id: str, query: str = "") -> dict:
    """Recall memories. If query is provided, filter by keyword match."""
    data = _load(profile_id)
    if not query:
        return data

    q = query.lower()
    filtered = {
        "facts": [f for f in data["facts"] if q in f["content"].lower() or q in f.get("category", "").lower()],
        "conversations": [c for c in data["conversations"] if q in c["summary"].lower()],
    }
    return filtered


def get_context_for_prompt(profile_id: str) -> str:
    """Build a memory context string to inject into the system prompt."""
    data = _load(profile_id)
    parts = []

    if data["facts"]:
        parts.append("MEMORIAS PERSISTENTES (fatos que voce salvou sobre este usuario):")
        for i, fact in enumerate(data["facts"]):
            cat = f"[{fact.get('category', 'geral')}]" if fact.get("category") else ""
            parts.append(f"  {i}. {cat} {fact['content']}")

    if data["conversations"]:
        # Show last 10 conversation summaries
        recent = data["conversations"][-10:]
        parts.append("\nCONVERSAS RECENTES (resumos automaticos):")
        for conv in recent:
            parts.append(f"  [{conv['date']}] {conv['summary']}")

    return "\n".join(parts) if parts else ""
