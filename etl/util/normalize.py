from typing import Dict, Any
from urllib.parse import urlparse


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).netloc
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def ensure_name(place: Dict[str, Any]) -> None:
    name = (place.get('name') or '').strip()
    if name and name != '(namnlös)':
        return
    cats = place.get('categories') or []
    host = _hostname(place.get('website') or '')
    if cats:
        place['name'] = f"{cats[0].replace('_',' ').title()} – {host}" if host else cats[0].replace('_',' ').title()
    elif host:
        place['name'] = host
    else:
        place['name'] = '(namnlös)'

