import json
from typing import List, Dict, Any
import requests


def fetch_hav_badplatser(url: str) -> List[Dict[str, Any]]:
    """Fetch bathing sites (badplatser) from a HAV/agency endpoint.

    The URL should point to a JSON or GeoJSON feed with coordinates and names.
    Only entries with a 'website' (or similar) are kept.
    """
    if not url:
        return []
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    places: List[Dict[str, Any]] = []

    # Try GeoJSON FeatureCollection
    if isinstance(data, dict) and data.get('type') == 'FeatureCollection':
        for f in data.get('features', []):
            props = f.get('properties', {}) or {}
            geom = f.get('geometry', {}) or {}
            coords = (geom.get('coordinates') or [None, None])
            lon, lat = (coords + [None, None])[:2]
            name = props.get('name') or props.get('namn') or 'Badplats'
            website = props.get('website') or props.get('url') or props.get('lank')
            if not website:
                continue
            places.append({
                'id': props.get('id') or props.get('badplats_id') or f"hav/{name}",
                'name': name,
                'categories': ['swimming'],
                'lat': lat,
                'lon': lon,
                'website': website,
                'source': {'name': 'HAV', 'url': url, 'license': 'Open data (check source)'},
                'amenities': [],
                'images': [],
                'opening_hours': None,
                'description': props.get('description') or props.get('beskrivning'),
            })
        return places

    # Try array of objects with lat/lon
    if isinstance(data, list):
        for it in data:
            if not isinstance(it, dict):
                continue
            lat = it.get('lat') or it.get('latitude')
            lon = it.get('lon') or it.get('longitude')
            website = it.get('website') or it.get('url')
            if not website or lat is None or lon is None:
                continue
            places.append({
                'id': it.get('id') or f"hav/{it.get('name')}",
                'name': it.get('name') or it.get('namn') or 'Badplats',
                'categories': ['swimming'],
                'lat': float(lat),
                'lon': float(lon),
                'website': website,
                'source': {'name': 'HAV', 'url': url, 'license': 'Open data (check source)'},
                'amenities': [],
                'images': [],
                'opening_hours': None,
                'description': it.get('description') or it.get('beskrivning'),
            })
        return places

    return []

