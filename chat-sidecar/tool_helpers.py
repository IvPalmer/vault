"""
Shared helpers for Vault MCP tools.
Provides httpx client, API base URL, and request helper.
"""
import httpx
import os

VAULT_API = os.environ.get("VAULT_API_URL", "http://127.0.0.1:8001/api")
REMINDERS_API = os.environ.get("REMINDERS_API_URL", "http://127.0.0.1:5177/api/home/reminders")
# Override Host header sent to backend (e.g. "vault.grooveops.dev") so Django
# ALLOWED_HOSTS accepts the request when the in-cluster service name (e.g.
# "backend") is not in ALLOWED_HOSTS.
VAULT_API_HOST = os.environ.get("VAULT_API_HOST")

# Shared async client (reused across tool calls)
_client: httpx.AsyncClient | None = None


def _headers(profile_id: str, extra: dict | None = None) -> dict:
    h = {"X-Profile-ID": profile_id}
    if VAULT_API_HOST:
        h["Host"] = VAULT_API_HOST
    if extra:
        h.update(extra)
    return h


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
        headers=_headers(profile_id),
        params=params or {},
    )
    resp.raise_for_status()
    return resp.json()


async def vault_post(path: str, profile_id: str, data: dict | None = None) -> dict:
    """POST request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.post(
        f"{VAULT_API}{path}",
        headers=_headers(profile_id, {"Content-Type": "application/json"}),
        json=data or {},
    )
    resp.raise_for_status()
    return resp.json()


async def vault_put(path: str, profile_id: str, data: dict) -> dict:
    """PUT request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.put(
        f"{VAULT_API}{path}",
        headers=_headers(profile_id, {"Content-Type": "application/json"}),
        params={"profile_id": profile_id},
        json=data,
    )
    resp.raise_for_status()
    return resp.json()


async def vault_patch(path: str, profile_id: str, data: dict) -> dict:
    """PATCH request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.patch(
        f"{VAULT_API}{path}",
        headers=_headers(profile_id, {"Content-Type": "application/json"}),
        json=data,
    )
    resp.raise_for_status()
    return resp.json()


async def vault_delete(path: str, profile_id: str) -> dict | None:
    """DELETE request to Vault API with profile scoping."""
    client = get_client()
    resp = await client.delete(
        f"{VAULT_API}{path}",
        headers=_headers(profile_id),
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
