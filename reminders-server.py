#!/usr/bin/env python3
"""
Host-side sidecar server for Apple Reminders + Calendar.
Runs OUTSIDE Docker on macOS — uses a compiled Swift EventKit helper
for reminders and osascript for Apple Calendar access.

Vite proxies:
  /api/home/reminders/*  → this server on port 5176
  /api/home/calendar/*   → this server on port 5176

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
        elif path == '/api/home/calendar/calendars':
            self._get_calendars()
        elif path == '/api/home/calendar/events':
            self._get_calendar_events(parsed)
        elif path == '/api/home/calendar/status':
            self._get_calendar_status()
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
        elif path == '/api/home/calendar/add-event':
            self._add_calendar_event(body)
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

    # ═══════════════════════════════════════════════════════
    # CALENDAR (via osascript / Apple Calendar)
    # ═══════════════════════════════════════════════════════

    def _run_osascript(self, script, timeout=15):
        """Run an AppleScript and return stdout."""
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def _get_calendar_status(self):
        """GET /api/home/calendar/status/ — always authenticated (local Apple Calendar)."""
        self._json_response({'authenticated': True, 'source': 'apple_calendar'})

    def _get_calendars(self):
        """GET /api/home/calendar/calendars/ — list all calendars."""
        script = 'tell application "Calendar" to get name of every calendar'
        try:
            stdout, stderr, rc = self._run_osascript(script)
            if rc != 0:
                self._json_response({'error': stderr or 'Failed to list calendars'}, 500)
                return
            names = [n.strip() for n in stdout.split(',') if n.strip()]
            self._json_response({'calendars': names})
        except subprocess.TimeoutExpired:
            self._json_response({'error': 'Calendar request timed out'}, 504)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def _get_calendar_events(self, parsed):
        """GET /api/home/calendar/events/?time_min=YYYY-MM-DD&time_max=YYYY-MM-DD[&calendars=R&R,Work]"""
        params = parse_qs(parsed.query)
        time_min = params.get('time_min', [None])[0]
        time_max = params.get('time_max', [None])[0]
        cal_filter = params.get('calendars', [None])[0]  # comma-separated

        if not time_min or not time_max:
            self._json_response({'error': 'time_min and time_max required (YYYY-MM-DD)'}, 400)
            return

        # Build AppleScript to fetch events in date range
        # AppleScript date format: "YYYY-MM-DD" needs to be converted
        cal_clause = ''
        if cal_filter:
            cal_names = [n.strip() for n in cal_filter.split(',')]
            conditions = ' or '.join(
                f'name of its calendar is "{n}"' for n in cal_names
            )
            cal_clause = f'whose ({conditions})'

        script = f'''
set startDate to current date
set year of startDate to {time_min[:4]}
set month of startDate to {int(time_min[5:7])}
set day of startDate to {int(time_min[8:10])}
set hours of startDate to 0
set minutes of startDate to 0
set seconds of startDate to 0

set endDate to current date
set year of endDate to {time_max[:4]}
set month of endDate to {int(time_max[5:7])}
set day of endDate to {int(time_max[8:10])}
set hours of endDate to 23
set minutes of endDate to 59
set seconds of endDate to 59

tell application "Calendar"
    set eventList to {{}}
    set allEvents to (every event of every calendar whose start date >= startDate and start date <= endDate)
    repeat with calEvents in allEvents
        repeat with evt in calEvents
            set evtStart to start date of evt
            set evtEnd to end date of evt
            set evtTitle to summary of evt
            set evtAllDay to allday event of evt
            set evtLoc to ""
            try
                set evtLoc to location of evt
            end try
            set evtCal to name of calendar of evt
            -- Format: title|||start|||end|||allday|||location|||calendar
            set y1 to year of evtStart as text
            set m1 to text -2 thru -1 of ("0" & ((month of evtStart as number) as text))
            set d1 to text -2 thru -1 of ("0" & (day of evtStart as text))
            set h1 to text -2 thru -1 of ("0" & (hours of evtStart as text))
            set n1 to text -2 thru -1 of ("0" & (minutes of evtStart as text))
            set y2 to year of evtEnd as text
            set m2 to text -2 thru -1 of ("0" & ((month of evtEnd as number) as text))
            set d2 to text -2 thru -1 of ("0" & (day of evtEnd as text))
            set h2 to text -2 thru -1 of ("0" & (hours of evtEnd as text))
            set n2 to text -2 thru -1 of ("0" & (minutes of evtEnd as text))
            set startStr to y1 & "-" & m1 & "-" & d1 & "T" & h1 & ":" & n1
            set endStr to y2 & "-" & m2 & "-" & d2 & "T" & h2 & ":" & n2
            set evtLine to evtTitle & "|||" & startStr & "|||" & endStr & "|||" & (evtAllDay as text) & "|||" & evtLoc & "|||" & evtCal
            set end of eventList to evtLine
        end repeat
    end repeat
    set AppleScript's text item delimiters to linefeed
    return eventList as text
end tell
'''
        try:
            stdout, stderr, rc = self._run_osascript(script, timeout=30)
            if rc != 0:
                self._json_response({'error': stderr or 'Failed to fetch events'}, 500)
                return

            events = []
            cal_names_filter = None
            if cal_filter:
                cal_names_filter = set(n.strip() for n in cal_filter.split(','))

            for line in stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                parts = line.split('|||')
                if len(parts) < 6:
                    continue
                title, start, end, all_day, location, calendar = (
                    parts[0], parts[1], parts[2], parts[3], parts[4], parts[5],
                )
                # Filter by calendar if specified
                if cal_names_filter and calendar not in cal_names_filter:
                    continue

                is_all_day = all_day.lower() == 'true'
                evt = {
                    'title': title,
                    'start': start[:10] if is_all_day else start,
                    'end': end[:10] if is_all_day else end,
                    'all_day': is_all_day,
                    'location': location if location != 'missing value' else '',
                    'calendar': calendar,
                }
                events.append(evt)

            self._json_response({'events': events, 'count': len(events)})
        except subprocess.TimeoutExpired:
            self._json_response({'error': 'Calendar request timed out'}, 504)
        except Exception as e:
            self._json_response({'error': str(e)}, 500)

    def _add_calendar_event(self, body):
        """POST /api/home/calendar/add-event/ {calendar, title, start, end}"""
        calendar_name = body.get('calendar', 'R&R')
        title = body.get('title', '').strip()
        start = body.get('start', '')  # YYYY-MM-DDTHH:MM
        end = body.get('end', '')

        if not title or not start:
            self._json_response({'error': 'title and start required'}, 400)
            return

        if not end:
            end = start

        # Parse start/end
        sy, sm, sd = start[:4], int(start[5:7]), int(start[8:10])
        sh, sn = int(start[11:13]), int(start[14:16]) if len(start) > 11 else (0, 0)
        ey, em, ed = end[:4], int(end[5:7]), int(end[8:10])
        eh, en_ = int(end[11:13]), int(end[14:16]) if len(end) > 11 else (sh + 1, sn)

        script = f'''
tell application "Calendar"
    set theCal to first calendar whose name is "{calendar_name}"

    set startDate to current date
    set year of startDate to {sy}
    set month of startDate to {sm}
    set day of startDate to {sd}
    set hours of startDate to {sh}
    set minutes of startDate to {sn}
    set seconds of startDate to 0

    set endDate to current date
    set year of endDate to {ey}
    set month of endDate to {em}
    set day of endDate to {ed}
    set hours of endDate to {eh}
    set minutes of endDate to {en_}
    set seconds of endDate to 0

    make new event at end of events of theCal with properties {{summary:"{title}", start date:startDate, end date:endDate}}
    return "ok"
end tell
'''
        try:
            stdout, stderr, rc = self._run_osascript(script)
            if rc != 0:
                self._json_response({'error': stderr or 'Failed to create event'}, 500)
            else:
                self._json_response({'ok': True, 'title': title, 'calendar': calendar_name}, 201)
        except subprocess.TimeoutExpired:
            self._json_response({'error': 'Calendar request timed out'}, 504)
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
