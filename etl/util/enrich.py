from typing import List, Dict, Any
import re
import requests
from bs4 import BeautifulSoup


def _fetch(url: str, timeout: int = 12) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'FriluftBot/0.1 (+https://github.com/perwinroth/friluft)'
        })
        r.raise_for_status()
        return r.text
    except Exception:
        return ''


def _first_attr(soup: BeautifulSoup, selectors: List[str], attr: str) -> str:
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get(attr):
            return el.get(attr)  # type: ignore
    return ''


def _first_text(soup: BeautifulSoup, selectors: List[str]) -> str:
    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ''


def enrich_places_opengraph(places: List[Dict[str, Any]], max_items: int = 200) -> None:
    count = 0
    for p in places:
        if count >= max_items:
            break
        url = p.get('website')
        if not isinstance(url, str) or not url:
            continue
        html = _fetch(url)
        if not html:
            continue
        count += 1
        try:
            soup = BeautifulSoup(html, 'lxml')
        except Exception:
            soup = BeautifulSoup(html, 'html.parser')

        title = _first_attr(soup, ['meta[property="og:title"]', 'meta[name="twitter:title"]'], 'content') or _first_text(soup, ['title', 'h1'])
        desc = _first_attr(soup, ['meta[property="og:description"]', 'meta[name="description"]', 'meta[name="twitter:description"]'], 'content')
        image = _first_attr(soup, ['meta[property="og:image"]', 'meta[name="twitter:image"]'], 'content')

        # schema.org openingHours
        opening = ''
        for tag in soup.find_all(attrs={'itemprop': 'openingHours'}):
            txt = tag.get_text(strip=True)
            if txt:
                opening = txt
                break

        # Simple phone/email regex
        text = soup.get_text(" ", strip=True)
        phone = ''
        m = re.search(r"\+?\d[\d\s\-()]{6,}", text)
        if m:
            phone = m.group(0)

        p.setdefault('images', [])
        if image and image not in p['images']:
            p['images'].append(image)
        if desc and not p.get('description'):
            p['description'] = desc
        if title and p.get('name') and len(title) > len(p['name']):
            # Prefer richer title but keep original name if OG title looks spammy
            p['description'] = p.get('description') or title
        if opening and not p.get('opening_hours'):
            p['opening_hours'] = opening
        if phone:
            p.setdefault('contact', {})
            p['contact']['phone'] = p['contact'].get('phone') or phone

