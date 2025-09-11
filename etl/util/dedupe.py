from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse


def _norm_domain(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith('www.') else host
    except Exception:
        return ''


def _key(p: Dict[str, Any]) -> Tuple[str, str]:
    name = (p.get('name') or '').strip().lower()
    dom = _norm_domain(p.get('website') or '')
    return (name, dom)


def dedupe_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Dict[Tuple[str, str], Dict[str, Any]] = {}
    out: List[Dict[str, Any]] = []
    for p in places:
        k = _key(p)
        if k in seen:
            # merge categories and images
            prev = seen[k]
            prev['categories'] = sorted(set((prev.get('categories') or []) + (p.get('categories') or [])))
            prev['images'] = sorted(set((prev.get('images') or []) + (p.get('images') or [])))
            # prefer existing lat/lon; if missing, take new
            if prev.get('lat') is None and p.get('lat') is not None:
                prev['lat'] = p['lat']
            if prev.get('lon') is None and p.get('lon') is not None:
                prev['lon'] = p['lon']
            continue
        seen[k] = p
        out.append(p)
    return out

