#!/bin/bash
# ─── Vault Dev Environment ───────────────────────────────
# Starts all services needed for development:
#   1. Docker (Django + PostgreSQL) — assumes already running
#   2. Sidecar server (Apple Reminders via EventKit)
#   3. Vite dev server (frontend)
#
# Usage:
#   ./dev.sh          Start everything
#   ./dev.sh stop     Stop sidecar + Vite (Docker stays running)
# ──────────────────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"

stop_services() {
    echo "Stopping services..."
    lsof -ti:5176 2>/dev/null | xargs kill 2>/dev/null
    lsof -ti:5175 2>/dev/null | xargs kill 2>/dev/null
    echo "Done."
}

if [ "$1" = "stop" ]; then
    stop_services
    exit 0
fi

# ── Ensure helper binary is compiled ──
if [ ! -f "$DIR/reminders-helper" ]; then
    echo "Compiling EventKit helper..."
    swiftc -O "$DIR/reminders-helper.swift" -o "$DIR/reminders-helper"
fi

# ── Stop existing instances ──
stop_services

# ── Start sidecar (background, silent) ──
echo "Starting sidecar server on :5176..."
nohup python3 "$DIR/reminders-server.py" > /tmp/vault-sidecar.log 2>&1 &
SIDECAR_PID=$!

# Wait for sidecar to be ready
for i in 1 2 3 4 5; do
    if curl -s http://127.0.0.1:5176/api/home/reminders/lists/ > /dev/null 2>&1; then
        echo "  Sidecar ready (PID $SIDECAR_PID)"
        break
    fi
    sleep 1
done

# ── Start Vite (foreground so Ctrl+C kills everything) ──
echo "Starting Vite dev server on :5175..."
echo "──────────────────────────────────────"
trap "stop_services" EXIT

cd "$DIR" && npx vite --host
