import csv
import io
import json
from typing import List, Dict, Any
import requests


def fetch_municipal_dataset(url: str, kind: str = 'auto', activity: str = 'outdoor') -> List[Dict[str, Any]]:
    """Fetch a municipal open dataset (CSV or JSON/GeoJSON).

    Keeps entries with website/url and lat/lon and maps to the common place schema.
    """
    if not url:
        return []
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        content = r.content
        text = None
    except Exception:
        return []

    if kind == 'csv' or (kind == 'auto' and (url.endswith('.csv') or b',' in content[:128])):
        try:
            text = content.decode('utf-8', errors='replace')
            return _parse_csv(text, activity, url)
        except Exception:
            return []

    # JSON/GeoJSON
    try:
        data = json.loads(content.decode('utf-8', errors='replace'))
    except Exception:
        return []
    return _parse_json_like(data, activity, url)


def _parse_csv(text: str, activity: str, url: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        lat = row.get('lat') or row.get('latitude')
        lon = row.get('lon') or row.get('longitude') or row.get('long')
        website = row.get('website') or row.get('url') or row.get('lank')
        if not website or not lat or not lon:
            continue
        out.append({
            'id': row.get('id') or f"muni/{row.get('name') or row.get('namn')}",
            'name': row.get('name') or row.get('namn') or 'Plats',
            'categories': [activity],
            'lat': float(lat),
            'lon': float(lon),
            'website': website,
            'source': {'name': 'Municipal', 'url': url, 'license': 'Open data (check source)'},
            'amenities': [],
            'images': [],
            'opening_hours': row.get('opening_hours') or row.get('oppettider'),
            'description': row.get('description') or row.get('beskrivning'),
        })
    return out


def _parse_json_like(data: Any, activity: str, url: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    # GeoJSON FeatureCollection
    if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
        for f in data.get('features', []):
            props = f.get('properties', {}) or {}
            geom = f.get('geometry', {}) or {}
            coords = (geom.get('coordinates') or [None, None])
            lon, lat = (coords + [None, None])[:2]
            website = props.get('website') or props.get('url') or props.get('link')
            if not website or lat is None or lon is None:
                continue
            out.append({
                'id': props.get('id') or f"muni/{props.get('name')}",
                'name': props.get('name') or props.get('namn') or 'Plats',
                'categories': [activity],
                'lat': lat,
                'lon': lon,
                'website': website,
                'source': {'name': 'Municipal', 'url': url, 'license': 'Open data (check source)'},
                'amenities': [],
                'images': [],
                'opening_hours': props.get('opening_hours') or props.get('oppettider'),
                'description': props.get('description') or props.get('beskrivning'),
            })
        return out

    # Array of dicts
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                continue
            lat = it.get('lat') or it.get('latitude')
            lon = it.get('lon') or it.get('longitude')
            website = it.get('website') or it.get('url')
            if not website or lat is None or lon is None:
                continue
            out.append({
                'id': it.get('id') or f"muni/{it.get('name')}",
                'name': it.get('name') or it.get('namn') or 'Plats',
                'categories': [activity],
                'lat': float(lat),
                'lon': float(lon),
                'website': website,
                'source': {'name': 'Municipal', 'url': url, 'license': 'Open data (check source)'},
                'amenities': [],
                'images': [],
                'opening_hours': it.get('opening_hours') or it.get('oppettider'),
                'description': it.get('description') or it.get('beskrivning'),
            })
        return out
    return out

