import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Reuse OSM scraper internals
import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'scraper'))
import overpass_scraper  # type: ignore

from .sources.hav_badplatser import fetch_hav_badplatser
from .sources.municipal_generic import fetch_municipal_dataset
from .util.enrich import enrich_places_opengraph
from .util.dedupe import dedupe_places
from .util.bookable import detect_booking_type
from .util.normalize import ensure_name
from .sources.events_ical import fetch_events
from .sources.ckan_search import fetch_ckan_places
from .sources.municipal_list import fetch_municipal_list
from .crawl.municipal_crawler import crawl_municipality
from .util.linkcheck import check_links
from .util.openhours import is_open_now

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'


def place_from_osm_feature(f: Dict[str, Any]) -> Dict[str, Any]:
    p = f.get('properties', {})
    [lon, lat] = f.get('geometry', {}).get('coordinates', [None, None])
    tags = p.get('tags', {}) or {}
    return {
        'id': p.get('id'),
        'name': p.get('name'),
        'categories': p.get('categories', []),
        'lat': lat,
        'lon': lon,
        'website': p.get('link') or p.get('osm_url'),
        'source': {'name': 'OSM', 'url': p.get('osm_url'), 'license': 'ODbL'},
        'amenities': [],
        'images': [],
        'opening_hours': tags.get('opening_hours'),
        'open_now': True if (tags.get('opening_hours') or '').strip() == '24/7' else None,
        'description': None,
    }


def run_osm(endpoint: str) -> List[Dict[str, Any]]:
    cats = list(overpass_scraper.CATEGORY_DEFS.keys())
    feats = overpass_scraper.scrape(endpoint, cats)
    # website-only already enforced by overpass_scraper.to_feature
    return [place_from_osm_feature(f) for f in feats]


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    endpoint = os.environ.get('OVERPASS_ENDPOINT', overpass_scraper.DEFAULT_ENDPOINT)

    # 1) OSM
    osm_places = run_osm(endpoint)

    # 2) Hav badplatser (optional)
    hav_url = os.environ.get('HAV_BADPLATSER_URL', '').strip()
    hav_places = fetch_hav_badplatser(hav_url) if hav_url else []

    # 3) Municipal dataset (optional generic CSV/JSON)
    muni_url = os.environ.get('MUNICIPAL_DATASET_URL', '').strip()
    muni_type = os.environ.get('MUNICIPAL_DATASET_TYPE', 'auto')
    muni_activity = os.environ.get('MUNICIPAL_ACTIVITY', 'outdoor')
    muni_places = fetch_municipal_dataset(muni_url, muni_type, muni_activity) if muni_url else []

    # 4) CKAN discovery across municipal portals (optional)
    ckan_portals = os.environ.get('CKAN_PORTALS', '').strip()
    ckan_keywords = os.environ.get('CKAN_KEYWORDS', '').strip()
    ckan_activity_map = os.environ.get('CKAN_ACTIVITY_MAP', '').strip()
    ckan_max = int(os.environ.get('CKAN_MAX_PER_KEYWORD', '2'))
    ckan_places = []
    if ckan_portals and ckan_keywords:
        ckan_places = fetch_ckan_places(
            ckan_portals, ckan_keywords, activity_map_json=ckan_activity_map, max_resources_per_keyword=ckan_max
        )

    # Merge
    # 5) Extra direct dataset URLs (comma-separated), activity via EXTRA_ACTIVITY
    extra_urls = [u.strip() for u in os.environ.get('EXTRA_DATASET_URLS', '').split(',') if u.strip()]
    extra_activity = os.environ.get('EXTRA_ACTIVITY', 'outdoor')
    extra_places: List[Dict[str, Any]] = []
    if extra_urls:
        for u in extra_urls:
            kind = 'auto'
            if u.lower().endswith('.csv'):
                kind = 'csv'
            elif u.lower().endswith('.json') or 'geojson' in u.lower():
                kind = 'json'
            try:
                extra_places.extend(fetch_municipal_dataset(u, kind=kind, activity=extra_activity))
            except Exception:
                continue

    # 6) Optional municipal crawling (respect robots, limited scope)
    crawl_enabled = os.environ.get('ENABLE_MUNICIPAL_CRAWL', '0') == '1'
    crawl_list_url = os.environ.get('MUNI_LIST_URL', '').strip()
    crawl_sites = []
    crawl_places: List[Dict[str, Any]] = []
    if crawl_enabled:
        muni_list = fetch_municipal_list(crawl_list_url) if crawl_list_url else []
        # Fallback to a few known large municipalities if list not provided
        if not muni_list:
            muni_list = [
                {'name': 'Stockholm', 'website': 'https://www.stockholm.se'},
                {'name': 'Göteborg', 'website': 'https://www.goteborg.se'},
                {'name': 'Malmö', 'website': 'https://malmo.se'},
            ]
        crawl_max_sites = int(os.environ.get('CRAWL_MAX_SITES', '5'))
        crawl_max_pages = int(os.environ.get('CRAWL_MAX_PAGES', '25'))
        crawl_max_depth = int(os.environ.get('CRAWL_MAX_DEPTH', '2'))
        for m in muni_list[:crawl_max_sites]:
            site = (m.get('website') or '').strip()
            if site:
                crawl_sites.append(site)
                try:
                    crawl_places.extend(crawl_municipality(site, max_pages=crawl_max_pages, max_depth=crawl_max_depth))
                except Exception:
                    continue

    places = osm_places + hav_places + muni_places + ckan_places + extra_places + crawl_places

    # Dedupe
    places = dedupe_places(places)

    # Enrich from website OpenGraph/schema.org (limited per run)
    max_enrich = int(os.environ.get('ENRICH_MAX', '200'))
    enrich_places_opengraph(places, max_items=max_enrich)

    # Detect booking capability
    for p in places:
        bt = detect_booking_type(p.get('website'))
        if bt:
            p['bookable'] = True
            p['bookingType'] = bt

    # Ensure all places have a better-than-default name
    for p in places:
        ensure_name(p)

    # Link checks (limit to avoid long runs)
    max_linkcheck = int(os.environ.get('LINKCHECK_MAX', '200'))
    sample = [pl for pl in places if pl.get('website')][:max_linkcheck]
    results = check_links([pl['website'] for pl in sample], concurrency=int(os.environ.get('LINKCHECK_CONCURRENCY', '10')))
    for pl, res in zip(sample, results):
        pl['link_ok'] = bool(res.get('ok'))
        if res.get('status') is not None:
            pl['link_status'] = res.get('status')
        if res.get('final') and res.get('final') != pl.get('website'):
            pl['website_final'] = res.get('final')

    # Opening-hours evaluation (basic): compute open_now where possible
    for pl in places:
        oh = (pl.get('opening_hours') or '').strip()
        if not oh:
            continue
        if oh.lower() == '24/7':
            pl['open_now'] = True
        else:
            val = is_open_now(oh)
            if val is not None:
                pl['open_now'] = val

    # Write combined JSON and GeoJSON for the map
    (DATA_DIR / 'places.json').write_text(json.dumps(places, ensure_ascii=False), encoding='utf-8')

    # Build GeoJSON for the map from combined places
    features = []
    for idx, pl in enumerate(places):
        if pl.get('lat') is None or pl.get('lon') is None:
            continue
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [pl['lon'], pl['lat']]},
            'properties': {
                'id': pl.get('id') or f'place/{idx}',
                'name': pl.get('name'),
                'categories': pl.get('categories', []),
                'link': pl.get('website'),
                'osm_url': pl.get('source', {}).get('url'),
                'bookable': pl.get('bookable', False),
                'open_now': pl.get('open_now', None),
                'link_ok': pl.get('link_ok', None),
            },
        })
    (DATA_DIR / 'lawnmover.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, ensure_ascii=False), encoding='utf-8')

    # Events (optional via ICS feeds)
    ical_env = os.environ.get('EVENT_ICAL_URLS', '').strip()
    events: List[Dict[str, Any]] = []
    if ical_env:
        urls = [u.strip() for u in ical_env.split(',') if u.strip()]
        events = fetch_events(urls)
        (DATA_DIR / 'events.json').write_text(json.dumps(events, ensure_ascii=False), encoding='utf-8')

    print(
        'OSM:', len(osm_places),
        'HAV:', len(hav_places),
        'Muni:', len(muni_places),
        'CKAN:', len(ckan_places),
        'Extra:', len(extra_places), 'Crawl:', len(crawl_places), 'Total (deduped):', len(places),
        'Events:', len(events)
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
