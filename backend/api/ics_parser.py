"""
ICS/iCal feed parser — fetches and parses .ics URLs into event dicts
compatible with the calendar events API response format.
"""
import logging
from datetime import datetime, date, timedelta, timezone
from urllib.parse import unquote

import requests

logger = logging.getLogger(__name__)


def fetch_and_parse(url: str, time_min: str, time_max: str, calendar_name: str, color: str) -> list[dict]:
    """Fetch an ICS feed URL and return events within the given date range.

    Args:
        url: ICS feed URL
        time_min: Start date (YYYY-MM-DD or ISO datetime)
        time_max: End date (YYYY-MM-DD or ISO datetime)
        calendar_name: Display name for the calendar
        color: Hex color for events

    Returns:
        List of event dicts matching the calendar API format.
    """
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Vault/1.0',
            'Accept': 'text/calendar',
        })
        resp.raise_for_status()
        text = resp.text
    except Exception as e:
        logger.warning(f'Failed to fetch ICS feed {calendar_name}: {e}')
        return []

    # Parse date range
    range_start = _parse_date(time_min)
    range_end = _parse_date(time_max)
    if range_end and not isinstance(range_end, datetime):
        range_end = datetime.combine(range_end, datetime.max.time())

    events = []
    for vevent in _extract_vevents(text):
        evt = _parse_vevent(vevent)
        if not evt:
            continue

        # Filter by date range
        evt_start = evt.get('_start_dt')
        if evt_start and range_start and range_end:
            if isinstance(evt_start, date) and not isinstance(evt_start, datetime):
                evt_dt = datetime.combine(evt_start, datetime.min.time())
            else:
                evt_dt = evt_start.replace(tzinfo=None) if hasattr(evt_start, 'replace') and evt_start.tzinfo else evt_start
            range_s = range_start.replace(tzinfo=None) if isinstance(range_start, datetime) and range_start.tzinfo else range_start
            range_e = range_end.replace(tzinfo=None) if isinstance(range_end, datetime) and range_end.tzinfo else range_end
            if isinstance(range_s, date) and not isinstance(range_s, datetime):
                range_s = datetime.combine(range_s, datetime.min.time())
            if evt_dt > range_e or evt_dt < range_s:
                continue

        # Remove internal fields
        evt.pop('_start_dt', None)

        evt['calendar'] = calendar_name
        evt['calendar_color'] = color
        events.append(evt)

    return events


def _parse_date(s: str):
    """Parse a date string (YYYY-MM-DD or ISO datetime)."""
    if not s:
        return None
    try:
        if 'T' in s:
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        return datetime.strptime(s[:10], '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _extract_vevents(ics_text: str) -> list[str]:
    """Extract raw VEVENT blocks from ICS text."""
    # Unfold continuation lines (RFC 5545: lines starting with space/tab continue previous)
    lines = ics_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    unfolded = []
    for line in lines:
        if line.startswith((' ', '\t')) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)

    blocks = []
    current = None
    for line in unfolded:
        if line.strip().upper() == 'BEGIN:VEVENT':
            current = []
        elif line.strip().upper() == 'END:VEVENT' and current is not None:
            blocks.append(current)
            current = None
        elif current is not None:
            current.append(line)
    return blocks


def _parse_vevent(lines: list[str]) -> dict | None:
    """Parse a VEVENT block into an event dict."""
    props = {}
    for line in lines:
        if ':' not in line:
            continue
        key_part, _, value = line.partition(':')
        # Key might have params like DTSTART;TZID=America/Sao_Paulo
        key = key_part.split(';')[0].upper()
        props.setdefault(key, value)

    summary = props.get('SUMMARY', '').strip()
    if not summary:
        return None

    # Parse start/end
    dtstart_raw = props.get('DTSTART', '')
    dtend_raw = props.get('DTEND', '')

    start_dt = _parse_ics_datetime(dtstart_raw)
    end_dt = _parse_ics_datetime(dtend_raw)

    if not start_dt:
        return None

    # Detect all-day events (date only, no time component)
    all_day = isinstance(start_dt, date) and not isinstance(start_dt, datetime)

    # Format for API response
    if all_day:
        start_str = start_dt.isoformat()
        end_str = end_dt.isoformat() if end_dt else start_str
    else:
        start_str = start_dt.isoformat() if isinstance(start_dt, datetime) else start_dt.isoformat()
        end_str = end_dt.isoformat() if end_dt else ''

    location = props.get('LOCATION', '').replace('\\n', '\n').replace('\\,', ',').strip()
    description = props.get('DESCRIPTION', '').replace('\\n', '\n').replace('\\,', ',').strip()

    return {
        'title': _unescape(summary),
        'start': start_str,
        'end': end_str,
        'all_day': all_day,
        'location': _unescape(location),
        'description': _unescape(description)[:200] if description else '',
        '_start_dt': start_dt,
    }


def _parse_ics_datetime(raw: str):
    """Parse an ICS DTSTART/DTEND value."""
    if not raw:
        return None
    raw = raw.strip()

    # Date only: 20260405
    if len(raw) == 8 and raw.isdigit():
        try:
            return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
        except ValueError:
            return None

    # DateTime: 20260405T140000Z or 20260405T140000
    raw = raw.replace('Z', '')
    if 'T' in raw:
        raw = raw.replace('-', '').replace(':', '')
        try:
            return datetime.strptime(raw[:15], '%Y%m%dT%H%M%S')
        except ValueError:
            return None

    # Fallback: try date
    try:
        return date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    except (ValueError, IndexError):
        return None


def _unescape(s: str) -> str:
    """Unescape ICS text values."""
    return s.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
