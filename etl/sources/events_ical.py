from typing import List, Dict, Any
from datetime import datetime, timezone
import requests

try:
    from icalendar import Calendar
except Exception:
    Calendar = None  # type: ignore


def _to_iso(dtval) -> str:
    if hasattr(dtval, 'dt'):
        v = dtval.dt
    else:
        v = dtval
    if isinstance(v, datetime):
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat()
    return str(v)


def fetch_events(urls: List[str]) -> List[Dict[str, Any]]:
    if not Calendar:
        return []
    out: List[Dict[str, Any]] = []
    for url in urls:
        if not url:
            continue
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            cal = Calendar.from_ical(r.content)
        except Exception:
            continue
        for comp in cal.walk('VEVENT'):
            name = str(comp.get('summary', '')).strip() or 'Evenemang'
            dtstart = comp.get('dtstart')
            dtend = comp.get('dtend')
            loc = str(comp.get('location', '')).strip() or 'Sverige'
            desc = str(comp.get('description', '')).strip()
            url_ev = str(comp.get('url', '')).strip()
            out.append({
                'name': name,
                'date': _to_iso(dtstart) if dtstart else '',
                'location': loc,
                'description': desc,
                'eventType': 'evenemang',
                'registrationUrl': url_ev or None,
            })
    # basic sort by date string
    out.sort(key=lambda e: e.get('date') or '')
    return out

