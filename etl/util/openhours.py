from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import List, Tuple, Optional


WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
WD_INDEX = {wd: i for i, wd in enumerate(WEEKDAYS)}


def _parse_time(s: str) -> Optional[time]:
    try:
        hh, mm = s.split(":")
        return time(int(hh), int(mm))
    except Exception:
        return None


def _expand_days(spec: str) -> List[int]:
    days: List[int] = []
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    for p in parts:
        if "-" in p:
            a, b = [x.strip() for x in p.split("-")]
            if a in WD_INDEX and b in WD_INDEX:
                ia, ib = WD_INDEX[a], WD_INDEX[b]
                if ia <= ib:
                    days.extend(list(range(ia, ib + 1)))
                else:
                    days.extend(list(range(ia, 7)))
                    days.extend(list(range(0, ib + 1)))
        elif p in WD_INDEX:
            days.append(WD_INDEX[p])
    # unique preserve order
    seen = set()
    out: List[int] = []
    for d in days:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


def is_open_now(opening: str, now: Optional[datetime] = None, tz: str = "Europe/Stockholm") -> Optional[bool]:
    """
    Evaluate a limited subset of OSM opening_hours to determine if open now.
    Supports:
      - "24/7"
      - day specs like "Mo-Su 08:00-18:00" or "Mo-Fr 09:00-17:00; Sa 10:00-14:00; Su off"
    Returns True/False if confidently determined, or None if unknown/unsupported.
    """
    if not opening:
        return None
    opening = opening.strip()
    if opening.lower() == "24/7":
        return True
    if now is None:
        now = datetime.now(ZoneInfo(tz))
    wd = now.weekday()  # Monday=0
    current = now.time()

    # Split by semicolon into rules
    rules = [r.strip() for r in opening.split(";") if r.strip()]
    any_rule = False
    for r in rules:
        # off rules
        if r.endswith(" off"):
            daypart = r[:-4].strip()
            days = _expand_days(daypart)
            if wd in days:
                # explicitly off today
                any_rule = True
                continue
            else:
                # off other days; ignore
                continue
        # Patterns like "Mo-Fr 08:00-18:00" OR multiple spans: "Mo-Fr 08:00-12:00,13:00-17:00"
        m = re.match(r"^([A-Za-z,\-]+)\s+(.+)$", r)
        if not m:
            continue
        days_spec, times_part = m.groups()
        days = _expand_days(days_spec)
        spans = [t.strip() for t in times_part.split(',') if t.strip()]
        valid_span = False
        for span in spans:
            m2 = re.match(r"^(\d{2}:\d{2})-(\d{2}:\d{2})$", span)
            if not m2:
                continue
            start_s, end_s = m2.groups()
            start_t = _parse_time(start_s)
            end_t = _parse_time(end_s)
            if not start_t or not end_t:
                continue
            valid_span = True
            if wd in days and start_t <= current <= end_t:
                return True
        if valid_span:
            any_rule = True
    # If we had rules and none matched as open, assume closed
    if any_rule:
        return False
    # Unknown format
    return None
