#!/bin/bash
# ─── Vault Service Manager ─────────────────────────────────
# Manages all Vault services: Docker (db + backend) and
# macOS launchd agents (frontend + reminders sidecar).
#
# Usage:
#   ./vault.sh start    Start all services
#   ./vault.sh stop     Stop all services
#   ./vault.sh restart  Restart all services
#   ./vault.sh status   Show status of all services
#   ./vault.sh logs     Tail all log files
#   ./vault.sh install  Register launchd agents (run once)
#   ./vault.sh uninstall Remove launchd agents
# ──────────────────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
SIDECAR_PLIST="$HOME/Library/LaunchAgents/com.vault.sidecar.plist"
FRONTEND_PLIST="$HOME/Library/LaunchAgents/com.vault.frontend.plist"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

check_port() {
    lsof -ti:"$1" > /dev/null 2>&1
}

get_lan_ip() {
    ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "unknown"
}

# ── Compile EventKit helper if needed ──
ensure_helper() {
    if [ ! -f "$DIR/reminders-helper" ]; then
        echo -e "${YELLOW}Compiling EventKit helper...${NC}"
        swiftc -O "$DIR/reminders-helper.swift" -o "$DIR/reminders-helper"
    fi
}

case "${1:-status}" in

start)
    echo -e "${CYAN}═══ Starting Vault ═══${NC}"

    # Compile helper if needed
    ensure_helper

    # Docker services
    echo -e "${CYAN}Starting Docker services (db + backend)...${NC}"
    cd "$DIR" && docker compose up -d db backend
    echo -e "${GREEN}  ✓ Docker services started${NC}"

    # Launchd agents
    echo -e "${CYAN}Starting launchd agents...${NC}"
    launchctl load "$SIDECAR_PLIST" 2>/dev/null
    launchctl load "$FRONTEND_PLIST" 2>/dev/null

    # Wait for services
    echo -e "${CYAN}Waiting for services...${NC}"
    for i in $(seq 1 15); do
        ALL_UP=true
        check_port 8001 || ALL_UP=false
        check_port 5175 || ALL_UP=false
        check_port 5176 || ALL_UP=false
        if $ALL_UP; then break; fi
        sleep 1
    done

    LAN_IP=$(get_lan_ip)
    echo ""
    echo -e "${GREEN}═══ Vault is running ═══${NC}"
    echo -e "  Frontend:  http://localhost:5175  |  http://$LAN_IP:5175"
    echo -e "  Backend:   http://localhost:8001"
    echo -e "  Sidecar:   http://localhost:5176"
    echo -e "  Database:  localhost:5432"
    echo ""
    ;;

stop)
    echo -e "${CYAN}═══ Stopping Vault ═══${NC}"

    # Launchd agents
    launchctl unload "$SIDECAR_PLIST" 2>/dev/null
    launchctl unload "$FRONTEND_PLIST" 2>/dev/null
    echo -e "${GREEN}  ✓ Launchd agents stopped${NC}"

    # Kill any remaining processes on those ports
    lsof -ti:5175 2>/dev/null | xargs kill 2>/dev/null
    lsof -ti:5176 2>/dev/null | xargs kill 2>/dev/null

    # Docker services
    cd "$DIR" && docker compose stop
    echo -e "${GREEN}  ✓ Docker services stopped${NC}"
    echo -e "${GREEN}═══ Vault stopped ═══${NC}"
    ;;

restart)
    "$0" stop
    sleep 2
    "$0" start
    ;;

status)
    echo -e "${CYAN}═══ Vault Status ═══${NC}"

    # Database
    if check_port 5432; then
        echo -e "  ${GREEN}● PostgreSQL${NC}        :5432  running"
    else
        echo -e "  ${RED}○ PostgreSQL${NC}        :5432  stopped"
    fi

    # Backend
    if check_port 8001; then
        echo -e "  ${GREEN}● Django Backend${NC}   :8001  running"
    else
        echo -e "  ${RED}○ Django Backend${NC}   :8001  stopped"
    fi

    # Frontend
    if check_port 5175; then
        echo -e "  ${GREEN}● Vite Frontend${NC}    :5175  running"
    else
        echo -e "  ${RED}○ Vite Frontend${NC}    :5175  stopped"
    fi

    # Sidecar
    if check_port 5176; then
        echo -e "  ${GREEN}● Reminders Sidecar${NC} :5176  running"
    else
        echo -e "  ${RED}○ Reminders Sidecar${NC} :5176  stopped"
    fi

    # Launchd status
    echo ""
    echo -e "${CYAN}Launchd Agents:${NC}"
    if launchctl list 2>/dev/null | grep -q "com.vault.sidecar"; then
        echo -e "  ${GREEN}● com.vault.sidecar${NC}   loaded"
    else
        echo -e "  ${RED}○ com.vault.sidecar${NC}   not loaded"
    fi
    if launchctl list 2>/dev/null | grep -q "com.vault.frontend"; then
        echo -e "  ${GREEN}● com.vault.frontend${NC}  loaded"
    else
        echo -e "  ${RED}○ com.vault.frontend${NC}  not loaded"
    fi

    # LAN access
    LAN_IP=$(get_lan_ip)
    echo ""
    echo -e "${CYAN}LAN Access:${NC}  http://$LAN_IP:5175"
    ;;

logs)
    echo -e "${CYAN}═══ Tailing Vault Logs (Ctrl+C to stop) ═══${NC}"
    tail -f /tmp/vault-sidecar.log /tmp/vault-frontend.log
    ;;

install)
    echo -e "${CYAN}═══ Installing Vault Services ═══${NC}"
    ensure_helper

    # Load launchd agents
    launchctl load "$SIDECAR_PLIST" 2>/dev/null && \
        echo -e "  ${GREEN}✓ Sidecar agent installed${NC}" || \
        echo -e "  ${YELLOW}⚠ Sidecar agent already loaded${NC}"

    launchctl load "$FRONTEND_PLIST" 2>/dev/null && \
        echo -e "  ${GREEN}✓ Frontend agent installed${NC}" || \
        echo -e "  ${YELLOW}⚠ Frontend agent already loaded${NC}"

    # Ensure Docker Desktop auto-starts (it does by default)
    echo -e "  ${GREEN}✓ Docker containers use restart: always/unless-stopped${NC}"
    echo ""
    echo -e "${GREEN}Done! Vault will auto-start on login and restart on crash.${NC}"
    echo -e "Docker Desktop must be set to 'Start on login' in its settings."
    ;;

uninstall)
    echo -e "${CYAN}═══ Uninstalling Vault Services ═══${NC}"
    launchctl unload "$SIDECAR_PLIST" 2>/dev/null
    launchctl unload "$FRONTEND_PLIST" 2>/dev/null
    echo -e "${GREEN}  ✓ Launchd agents unloaded${NC}"
    echo -e "  Plist files kept at ~/Library/LaunchAgents/"
    echo -e "  Docker containers still have restart policies."
    ;;

*)
    echo "Usage: $0 {start|stop|restart|status|logs|install|uninstall}"
    exit 1
    ;;
esac
