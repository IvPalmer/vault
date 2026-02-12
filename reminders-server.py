#!/usr/bin/env python3
"""
Host-side sidecar server for Apple Reminders.
Runs OUTSIDE Docker on macOS — uses a compiled Swift EventKit helper.

Vite proxies:
  /api/home/reminders/*  → this server on port 5176

Calendar is now handled by Google Calendar API via Django.

Usage:
    python3 reminders-server.py
"""

import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 5176
HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reminders-helper')

# Only show these lists on the Home screen (the shared R&R lists)
HOME_LISTS = ['R&R Tarefas', 'R&R Casa', 'R&R Compras']


def run_helper(*args, timeout=15):
    """Run the compiled Swift helper and return parsed JSON."""
    result = subprocess.run(
        [HELPER, *args],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        try:
            return json.loads(result.stdout)
        except Exception:
            return {'error': stderr or 'Helper failed'}
    return json.loads(result.stdout)


class SidecarHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json_response(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')

        if path == '/api/home/reminders':
            self._get_reminders(parsed)
        elif path == '/api/home/reminders/lists':
            self._get_lists()
        else:
            self._json_response({'error': 'Not found'}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == '/api/home/reminders/add':
            self._add_reminder(body)
        elif path == '/api/home/reminders/complete':
            self._complete_reminder(body)
        else:
            self._json_response({'error': 'Not found'}, 404)

    # ═══════════════════════════════════════════════════════
    # REMINDERS
    # ═══════════════════════════════════════════════════════

    def _get_reminders(self, parsed):
        params = parse_qs(parsed.query)
        list_name = params.get('list', ['R&R Tarefas'])[0]
        try:
            data = run_helper('get', list_name)
            if 'error' in data:
                self._json_response(data, 500)
            else:
                self._json_response(data)
        except subprocess.TimeoutExpired:
            self._json_response({'error': 'Reminders request timed out'}, 504)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def _get_lists(self):
        try:
            data = run_helper('lists')
            if 'error' in data:
                self._json_response(data, 500)
                return
            all_lists = data.get('lists', [])
            filtered = [l for l in HOME_LISTS if l in all_lists]
            self._json_response({'lists': filtered if filtered else all_lists})
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def _add_reminder(self, body):
        list_name = body.get('list', 'R&R Tarefas')
        name = body.get('name', '').strip()
        if not name:
            self._json_response({'error': 'name is required'}, 400)
            return
        try:
            data = run_helper('add', list_name, name)
            if 'error' in data:
                self._json_response(data, 500)
            else:
                self._json_response(data, 201)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def _complete_reminder(self, body):
        list_name = body.get('list', 'R&R Tarefas')
        name = body.get('name', '').strip()
        if not name:
            self._json_response({'error': 'name is required'}, 400)
            return
        try:
            data = run_helper('complete', list_name, name)
            if 'error' in data:
                code = 404 if 'not found' in data.get('error', '').lower() else 500
                self._json_response(data, code)
            else:
                self._json_response(data)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def log_message(self, format, *args):
        print(f'[sidecar] {args[0]}')


if __name__ == '__main__':
    if not os.path.isfile(HELPER):
        print(f'Error: Helper binary not found at {HELPER}')
        print(f'Compile it first: swiftc -O reminders-helper.swift -o reminders-helper')
        sys.exit(1)

    server = HTTPServer(('127.0.0.1', PORT), SidecarHandler)
    print(f'Reminders sidecar running on http://127.0.0.1:{PORT}')
    print(f'Using EventKit helper: {HELPER}')
    print(f'Lists: {", ".join(HOME_LISTS)}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.server_close()
