"""
Sandbox — manages a git worktree for isolated code edits.

Lifecycle:
  1. ensure_worktree() — create/reset persistent worktree
  2. (agent runs with cwd=worktree_path)
  3. validate() — run vite build in worktree
  4. merge_back() — copy changed files to main repo
  5. discard() — reset worktree on failure
"""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path

MAIN_REPO = Path("/Users/palmer/Work/Dev/Vault")
WORKTREE_DIR = MAIN_REPO.parent / ".vault-sandbox"
WORKTREE_BRANCH = "sandbox/sidecar"


async def _run(cmd: list[str], cwd: str | None = None, timeout: int = 60) -> tuple[int, str, str]:
    """Run a command async, return (returncode, stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "timeout"
    return proc.returncode, stdout.decode(), stderr.decode()


async def ensure_worktree() -> Path:
    """Create or reset the sandbox worktree. Returns worktree path."""
    wt = WORKTREE_DIR

    if wt.exists():
        # Reset to match current HEAD
        await _run(["git", "checkout", "--", "."], cwd=str(wt))
        await _run(["git", "clean", "-fd"], cwd=str(wt))
        await _run(["git", "pull", "--rebase", "origin", "main"], cwd=str(wt))
    else:
        # Create worktree
        await _run(
            ["git", "worktree", "add", str(wt), "HEAD"],
            cwd=str(MAIN_REPO),
        )

    # Symlink node_modules to avoid npm install
    nm_link = wt / "node_modules"
    nm_src = MAIN_REPO / "node_modules"
    if not nm_link.exists() and nm_src.exists():
        nm_link.symlink_to(nm_src)

    return wt


async def validate(worktree: Path) -> tuple[bool, str]:
    """Run vite build in the worktree. Returns (success, output)."""
    rc, stdout, stderr = await _run(
        ["npx", "vite", "build", "--mode", "development"],
        cwd=str(worktree),
        timeout=120,
    )
    output = stdout + stderr
    return rc == 0, output


async def get_changed_files(worktree: Path) -> list[str]:
    """Get list of files modified in the worktree relative to HEAD."""
    rc, stdout, _ = await _run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(worktree),
    )
    if rc != 0:
        return []
    return [f.strip() for f in stdout.strip().split("\n") if f.strip()]


async def merge_back(worktree: Path) -> list[str]:
    """Copy changed files from worktree to main repo. Returns list of merged files."""
    changed = await get_changed_files(worktree)
    merged = []
    for rel_path in changed:
        src = worktree / rel_path
        dst = MAIN_REPO / rel_path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            merged.append(rel_path)
    return merged


async def discard(worktree: Path):
    """Reset worktree to clean state (discard all changes)."""
    await _run(["git", "checkout", "--", "."], cwd=str(worktree))
    await _run(["git", "clean", "-fd"], cwd=str(worktree))


# ---------------------------------------------------------------------------
# Edit-intent detection
# ---------------------------------------------------------------------------

# Keywords that suggest the user wants code/UI changes
_CODE_EDIT_SIGNALS = [
    # Portuguese
    "edita", "editar", "modifica", "modificar", "muda", "mudar", "altera", "alterar",
    "adiciona", "adicionar", "remove", "remover", "corrige", "corrigir", "arruma", "arrumar",
    "cria um", "cria uma", "criar um", "criar uma", "implementa", "implementar",
    "componente", "widget", "css", "estilo", "layout", "tela", "pagina",
    "calendario", "timeline", "botao", "botão", "menu", "sidebar", "header",
    "frontend", "react", "jsx", "html",
    # English
    "edit", "modify", "change", "add", "remove", "fix", "create a", "implement",
    "component", "style", "screen", "page", "button",
]


def needs_sandbox(message: str) -> bool:
    """Heuristic: does this message likely require source code edits?"""
    lower = message.lower()
    matches = sum(1 for kw in _CODE_EDIT_SIGNALS if kw in lower)
    return matches >= 2
