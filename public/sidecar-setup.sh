#!/bin/bash
# ─── Vault Reminders Sidecar Setup ───────────────────────
# Run this on any Mac to set up the Apple Reminders sidecar.
# It compiles the Swift helper and starts the server.
#
# Usage: curl -sL http://vault.local:5175/sidecar-setup.sh | bash
# ──────────────────────────────────────────────────────────

set -e

VAULT_DIR="$HOME/.vault-sidecar"
SIDECAR_PORT=5176

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Vault Reminders Sidecar Setup      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Create directory
mkdir -p "$VAULT_DIR"
cd "$VAULT_DIR"

# Download files from Vault server (assumes running on local network)
VAULT_HOST="${VAULT_HOST:-vault.local:5175}"

echo "[1/4] Downloading files..."

# Write the Swift helper inline (self-contained)
cat > reminders-helper.swift << 'SWIFT_EOF'
#!/usr/bin/env swift
import AppKit
import EventKit
import Foundation

let store = EKEventStore()
let semReminders = DispatchSemaphore(value: 0)
if #available(macOS 14.0, *) {
    store.requestFullAccessToReminders { _, _ in semReminders.signal() }
} else {
    store.requestAccess(to: .reminder) { _, _ in semReminders.signal() }
}
semReminders.wait()

let args = CommandLine.arguments
func findReminderList(named name: String) -> EKCalendar? {
    return store.calendars(for: .reminder).first { $0.title == name }
}
func outputJSON(_ obj: Any) {
    if let data = try? JSONSerialization.data(withJSONObject: obj, options: [.prettyPrinted]),
       let str = String(data: data, encoding: .utf8) { print(str) }
}
guard args.count >= 2 else {
    print("{\"error\": \"Usage: ./reminders-helper <command> [args...]\"}")
    exit(1)
}
switch args[1] {
case "lists":
    let calendars = store.calendars(for: .reminder)
    outputJSON(["lists": calendars.map { $0.title }])
case "get":
    guard args.count >= 3 else { print("{\"error\": \"Usage: get <list>\"}"); exit(1) }
    guard let cal = findReminderList(named: args[2]) else { print("{\"error\": \"List not found\"}"); exit(1) }
    let pred = store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: nil, calendars: [cal])
    var results: [EKReminder]?
    let sem = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: pred) { r in results = r; sem.signal() }
    sem.wait()
    let reminders = (results ?? []).map { r -> [String: Any] in
        var d: [String: Any] = ["name": r.title ?? "", "priority": r.priority]
        d["due_date"] = ""
        d["notes"] = r.notes ?? ""
        return d
    }
    outputJSON(["list": args[2], "reminders": reminders, "count": reminders.count])
case "add":
    guard args.count >= 4 else { print("{\"error\": \"Usage: add <list> <name>\"}"); exit(1) }
    guard let cal = findReminderList(named: args[2]) else { print("{\"error\": \"List not found\"}"); exit(1) }
    let reminder = EKReminder(eventStore: store)
    reminder.title = args[3]
    reminder.calendar = cal
    do { try store.save(reminder, commit: true); outputJSON(["ok": true]) }
    catch { print("{\"error\": \"\(error.localizedDescription)\"}"); exit(1) }
case "complete":
    guard args.count >= 4 else { print("{\"error\": \"Usage: complete <list> <name>\"}"); exit(1) }
    guard let cal = findReminderList(named: args[2]) else { print("{\"error\": \"List not found\"}"); exit(1) }
    let pred = store.predicateForIncompleteReminders(withDueDateStarting: nil, ending: nil, calendars: [cal])
    var results: [EKReminder]?
    let sem = DispatchSemaphore(value: 0)
    store.fetchReminders(matching: pred) { r in results = r; sem.signal() }
    sem.wait()
    if let match = results?.first(where: { $0.title == args[3] }) {
        match.isCompleted = true
        do { try store.save(match, commit: true); outputJSON(["ok": true]) }
        catch { print("{\"error\": \"\(error.localizedDescription)\"}"); exit(1) }
    } else { print("{\"error\": \"Reminder not found\"}"); exit(1) }
default:
    print("{\"error\": \"Unknown command\"}")
    exit(1)
}
SWIFT_EOF

cat > sidecar.py << 'PY_EOF'
#!/usr/bin/env python3
"""Vault Reminders Sidecar — serves Apple Reminders via HTTP."""
import json, os, subprocess, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 5176
HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reminders-helper')

def run_helper(*args, timeout=15):
    result = subprocess.run([HELPER, *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        try: return json.loads(result.stdout)
        except: return {'error': result.stderr.strip() or 'Helper failed'}
    return json.loads(result.stdout)

class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        params = parse_qs(parsed.query)
        if path == '/api/home/reminders':
            list_name = params.get('list', ['Reminders'])[0]
            try:
                data = run_helper('get', list_name)
                self._json(data, 500 if 'error' in data else 200)
            except Exception as e: self._json({'error': str(e)}, 500)
        elif path == '/api/home/reminders/lists':
            try:
                data = run_helper('lists')
                if 'error' in data: self._json(data, 500); return
                self._json({'lists': data.get('lists', [])})
            except Exception as e: self._json({'error': str(e)}, 500)
        elif path == '/health':
            self._json({'ok': True, 'port': PORT})
        else:
            self._json({'error': 'Not found'}, 404)
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        if path == '/api/home/reminders/add':
            list_name = body.get('list', 'Reminders')
            name = body.get('name', '').strip()
            if not name: self._json({'error': 'name required'}, 400); return
            try:
                data = run_helper('add', list_name, name)
                self._json(data, 500 if 'error' in data else 201)
            except Exception as e: self._json({'error': str(e)}, 500)
        elif path == '/api/home/reminders/complete':
            list_name = body.get('list', 'Reminders')
            name = body.get('name', '').strip()
            if not name: self._json({'error': 'name required'}, 400); return
            try:
                data = run_helper('complete', list_name, name)
                self._json(data, 500 if 'error' in data else 200)
            except Exception as e: self._json({'error': str(e)}, 500)
        else:
            self._json({'error': 'Not found'}, 404)
    def log_message(self, format, *args): print(f'[sidecar] {args[0]}')

if __name__ == '__main__':
    if not os.path.isfile(HELPER):
        print(f'Error: compile first — swiftc -O reminders-helper.swift -o reminders-helper')
        sys.exit(1)
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'Vault Reminders Sidecar running on port {PORT}')
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nStopped.'); server.server_close()
PY_EOF

echo "[2/4] Compiling Swift helper..."
swiftc -O reminders-helper.swift -o reminders-helper 2>&1

echo "[3/4] Testing Reminders access..."
./reminders-helper lists 2>&1 | head -5

# Create a LaunchAgent for auto-start
PLIST="$HOME/Library/LaunchAgents/com.vault.reminders-sidecar.plist"
echo "[4/4] Installing auto-start..."
cat > "$PLIST" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vault.reminders-sidecar</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${VAULT_DIR}/sidecar.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${VAULT_DIR}/sidecar.log</string>
    <key>StandardErrorPath</key>
    <string>${VAULT_DIR}/sidecar.log</string>
</dict>
</plist>
PLIST_EOF

launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"

echo ""
echo "Done! Sidecar is running on port $SIDECAR_PORT"
echo "It will auto-start on login."
echo ""
echo "To stop:  launchctl unload ~/Library/LaunchAgents/com.vault.reminders-sidecar.plist"
echo "To start: launchctl load ~/Library/LaunchAgents/com.vault.reminders-sidecar.plist"
echo "Logs:     tail -f ~/.vault-sidecar/sidecar.log"
echo ""
