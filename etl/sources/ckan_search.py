from typing import List, Dict, Any
import json
import requests

from .municipal_generic import fetch_municipal_dataset


def _norm_portals(val: str) -> List[str]:
    return [v.strip().rstrip('/') for v in val.split(',') if v.strip()]


def _norm_keywords(val: str) -> List[str]:
    return [v.strip() for v in val.split(',') if v.strip()]


def _guess_kind(url: str) -> str:
    u = url.lower()
    if u.endswith('.csv'):
        return 'csv'
    if u.endswith('.geojson') or 'geojson' in u:
        return 'json'
    if u.endswith('.json'):
        return 'json'
    return 'auto'


def search_ckan_resources(portal: str, keyword: str, rows: int = 10) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            f"{portal}/api/3/action/package_search",
            params={"q": keyword, "rows": rows},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        res = data.get('result', {})
        return res.get('results', [])
    except Exception:
        return []


def fetch_ckan_places(portals_csv: str, keywords_csv: str, activity_map_json: str = '', max_resources_per_keyword: int = 2) -> List[Dict[str, Any]]:
    portals = _norm_portals(portals_csv)
    keywords = _norm_keywords(keywords_csv)
    activity_map: Dict[str, str] = {}
    if activity_map_json:
        try:
            activity_map = json.loads(activity_map_json)
        except Exception:
            activity_map = {}

    places: List[Dict[str, Any]] = []
    for portal in portals:
        for kw in keywords:
            results = search_ckan_resources(portal, kw, rows=10)
            taken = 0
            for pkg in results:
                if taken >= max_resources_per_keyword:
                    break
                for res in pkg.get('resources', []) or []:
                    if taken >= max_resources_per_keyword:
                        break
                    url = res.get('url') or ''
                    if not url:
                        continue
                    kind = _guess_kind(url)
                    activity = activity_map.get(kw) or kw
                    try:
                        batch = fetch_municipal_dataset(url, kind=kind, activity=activity)
                        if batch:
                            places.extend(batch)
                            taken += 1
                    except Exception:
                        continue
    return places

