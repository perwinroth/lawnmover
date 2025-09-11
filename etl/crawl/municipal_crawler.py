from typing import List, Dict, Any, Set
from urllib.parse import urljoin, urlparse
from collections import deque
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

KEYWORD_CATEGORIES = {
    'utegym': 'gym',
    'badplats': 'swimming', 'bad': 'swimming',
    'motionsspår': 'running', 'elljusspår': 'running', 'spår': 'running',
    'leder': 'hiking', 'vandring': 'hiking', 'naturreservat': 'nature_reserve',
    'kanot': 'canoe_kayak', 'kajak': 'canoe_kayak', 'paddling': 'canoe_kayak',
}

RE_COORD = re.compile(r"(?P<lat>[5-6]\d\.\d+)[,\s]+(?P<lon>(?:1\d|2[0-5])\.\d+)")


def allowed_by_robots(base: str, path: str) -> bool:
    try:
        rp = RobotFileParser()
        rp.set_url(urljoin(base, '/robots.txt'))
        rp.read()
        return rp.can_fetch('LawnmoverBot', path)
    except Exception:
        return True


def extract_coords(html: str) -> Dict[str, float]:
    # Try JSON-LD
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            import json
            data = json.loads(script.get_text(strip=True))
            if isinstance(data, dict):
                geo = data.get('geo') or {}
                lat = geo.get('latitude'); lon = geo.get('longitude')
                if lat and lon:
                    return {'lat': float(lat), 'lon': float(lon)}
        except Exception:
            continue
    # Regex fallback
    m = RE_COORD.search(html)
    if m:
        return {'lat': float(m.group('lat')), 'lon': float(m.group('lon'))}
    return {}


def categorize(text: str) -> List[str]:
    text = text.lower()
    cats: Set[str] = set()
    for k, v in KEYWORD_CATEGORIES.items():
        if k in text:
            cats.add(v)
    return list(cats)


def crawl_municipality(site: str, max_pages: int = 25, max_depth: int = 2, delay: float = 0.5) -> List[Dict[str, Any]]:
    parsed = urlparse(site)
    base = f"{parsed.scheme}://{parsed.netloc}"
    seeds = [
        '/uppleva-och-gora', '/kultur-och-fritid', '/fritid-och-kultur', '/motion-och-fritid', '/idrott', '/bad', '/utegym', '/natur', '/leder'
    ]
    queue = deque()
    seen: Set[str] = set()
    for s in seeds:
        queue.append((urljoin(base, s), 0))
    queue.append((site, 0))
    results: List[Dict[str, Any]] = []
    fetched = 0
    headers = {'User-Agent': 'LawnmoverBot/0.1 (+https://github.com/perwinroth/lawnmover)'}

    while queue and fetched < max_pages:
        url, depth = queue.popleft()
        if depth > max_depth:
            continue
        if url in seen:
            continue
        seen.add(url)
        path = urlparse(url).path or '/'
        if not allowed_by_robots(base, path):
            continue
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code >= 400:
                continue
            html = r.text
            fetched += 1
        except Exception:
            continue
        cats = categorize(html)
        if cats:
            coords = extract_coords(html)
            place = {
                'id': url,
                'name': BeautifulSoup(html, 'html.parser').title.string if BeautifulSoup(html, 'html.parser').title else url,
                'categories': cats,
                'lat': coords.get('lat'),
                'lon': coords.get('lon'),
                'website': url,
                'source': {'name': 'MunicipalCrawler', 'url': site, 'license': 'Website (check terms)'},
                'amenities': [],
                'images': [],
                'opening_hours': None,
                'description': None,
            }
            results.append(place)
        # Enqueue internal links
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('#'):
                    continue
                next_url = urljoin(url, href)
                p2 = urlparse(next_url)
                if p2.netloc != parsed.netloc:
                    continue
                # Focus only on relevant sections to reduce noise
                if any(seg in p2.path.lower() for seg in ['uppleva', 'fritid', 'kultur', 'motion', 'idrott', 'bad', 'utegym', 'natur', 'leder']):
                    queue.append((next_url, depth + 1))
        except Exception:
            pass
        time.sleep(delay)
    return results
