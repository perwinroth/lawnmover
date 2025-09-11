import argparse
import json
import sys
import time
import random
from typing import Dict, List, Tuple, Any
from urllib.parse import urlparse

import requests


DEFAULT_ENDPOINT = "https://overpass-api.de/api/interpreter"
DEFAULT_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


# Category definitions with Overpass tag selectors.
# Each entry is a list of tag expressions to match; we will query node/way/relation for each.
CATEGORY_DEFS: Dict[str, List[str]] = {
    # Retail categories and known chains likely to sell robot lawnmowers in Sweden
    # Note: We intentionally cast a wider net via shop types and chain brands.
    # Filtering to require a website happens later in to_feature().
    "robot_mower_seller": [
        # Broad retail categories
        '["shop"="doityourself"]',
        '["shop"="hardware"]',
        '["shop"="garden_centre"]',
        '["shop"="agrarian"]',
        '["shop"="electronics"]',
        '["shop"="department_store"]',
        # Known Swedish chains (brand or name match)
        '["brand"~"^(Bauhaus|Hornbach|Byggmax|Jula|Granngården|Elgiganten|MediaMarkt|NetOnNet|Elon|Plantagen|XL-Bygg|XL Bygg|Beijer|Woody|Stark)$", i]',
        '["name"~"Bauhaus|Hornbach|Byggmax|Jula|Granngården|Elgiganten|Media ?Markt|Net ?On ?Net|Elon|Plantagen|XL[- ]?Bygg|Beijer|Woody|Stark", i]',
    ],
}


def build_category_query(area_alias: str, tag_expr: str) -> str:
    """Return an Overpass QL snippet that fetches node/way/relation with tag_expr in the given area.

    Example tag_expr: '["tourism"="camp_site"]'
    """
    return (
        f"node{tag_expr}(area.{area_alias});\n"
        f"way{tag_expr}(area.{area_alias});\n"
        f"relation{tag_expr}(area.{area_alias});\n"
    )


def run_overpass(endpoints: List[str], ql: str, retries: int = 3) -> Dict[str, Any]:
    headers = {
        "User-Agent": "LawnmoverScraper/0.1 (+https://github.com/perwinroth/lawnmover)",
        "Accept-Language": "sv,en;q=0.8",
    }
    eps = list(endpoints)
    last_err: Exception | None = None
    for attempt in range(retries):
        random.shuffle(eps)
        for ep in eps:
            try:
                resp = requests.post(ep, data={"data": ql}, headers=headers, timeout=180)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_err = e
                time.sleep(2 * (attempt + 1))
                continue
    if last_err:
        raise last_err
    return {"elements": []}


def choose_name(tags: Dict[str, str]) -> str:
    for k in ("name:sv", "name", "name:en", "ref"):
        v = tags.get(k)
        if v:
            return v
    return "(namnlös)"


def choose_website(tags: Dict[str, str], include_social: bool = True) -> str:
    for k in ("website", "contact:website", "url"):
        v = tags.get(k)
        if v:
            if v.startswith("http://") or v.startswith("https://"):
                return v
            return "https://" + v
    if include_social:
        for k in ("facebook", "contact:facebook", "instagram", "contact:instagram", "twitter", "contact:twitter"):
            v = tags.get(k)
            if not v:
                continue
            if v.startswith("http://") or v.startswith("https://"):
                return v
            h = v.strip("/")
            if "facebook" in k:
                return f"https://facebook.com/{h}"
            if "instagram" in k:
                return f"https://instagram.com/{h}"
            if "twitter" in k:
                return f"https://twitter.com/{h}"
    return ""


def osm_url(el: Dict[str, Any]) -> str:
    return f"https://www.openstreetmap.org/{el['type']}/{el['id']}"


def to_feature(el: Dict[str, Any], categories: List[str], include_social: bool = True) -> Dict[str, Any]:
    tags = el.get("tags", {})
    website = choose_website(tags, include_social=include_social)
    if not website:
        # Only keep features that have an explicit website/contact URL
        raise ValueError("Missing website link")
    # Coordinates
    if el.get("type") == "node":
        lat = el.get("lat")
        lon = el.get("lon")
    else:
        center = el.get("center") or {}
        lat = center.get("lat")
        lon = center.get("lon")
    if lat is None or lon is None:
        raise ValueError("Missing coordinates")

    name = choose_name(tags)
    fallback_link = osm_url(el)

    props = {
        "id": f"{el['type']}/{el['id']}",
        "name": name if name and name != "(namnlös)" else (
            (categories[0].replace('_', ' ').title() + f" – {hostname(website)}") if categories else hostname(website) or "(namnlös)"
        ),
        "categories": sorted(set(categories)),
        "link": website,
        "osm_url": fallback_link,
        "tags": tags,
    }
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def build_master_query(categories: List[str]) -> List[Tuple[str, str]]:
    # Build a list of (category, query) pairs
    pairs: List[Tuple[str, str]] = []
    for cat in categories:
        exprs = CATEGORY_DEFS.get(cat, [])
        if not exprs:
            continue
        combined = "".join(build_category_query("a", e) for e in exprs)
        ql = (
            "[out:json][timeout:180];\n"
            "area[\"ISO3166-1\"=\"SE\"][admin_level=2]->.a;\n"
            "(\n" + combined + ")\n"
            ";\nout tags center;\n"
        )
        pairs.append((cat, ql))
    return pairs


def scrape(endpoint: str, categories: List[str], include_social: bool = True, retries: int = 3) -> List[Dict[str, Any]]:
    # Accumulate elements and their categories by (type, id)
    elements: Dict[Tuple[str, int], Dict[str, Any]] = {}
    el_cats: Dict[Tuple[str, int], List[str]] = {}

    endpoints = [e.strip() for e in endpoint.split(',') if e.strip()] or DEFAULT_ENDPOINTS

    for cat, ql in build_master_query(categories):
        data = run_overpass(endpoints, ql, retries=retries)
        for el in data.get("elements", []):
            key = (el.get("type"), el.get("id"))
            if key not in elements:
                elements[key] = el
                el_cats[key] = []
            el_cats[key].append(cat)

    # Convert to GeoJSON features
    features: List[Dict[str, Any]] = []
    for key, el in elements.items():
        cats = el_cats.get(key, [])
        try:
            feat = to_feature(el, cats, include_social=include_social)
            features.append(feat)
        except Exception:
            # Skip elements without usable coordinates
            continue
    return features


def write_geojson(features: List[Dict[str, Any]], out_path: str) -> None:
    fc = {"type": "FeatureCollection", "features": features}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Scrape Swedish robot lawnmower sellers from OSM via Overpass")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Overpass API endpoint (comma-separated to rotate)")
    parser.add_argument(
        "--categories",
        default=",".join(CATEGORY_DEFS.keys()),
        help="Comma-separated categories to include",
    )
    parser.add_argument("--out", default="data/lawnmover.geojson", help="Output GeoJSON path")
    parser.add_argument("--include-social", action="store_true", help="Allow social profile URLs if no website present")
    parser.add_argument("--retries", type=int, default=3, help="Retries per Overpass query across endpoints")
    args = parser.parse_args(argv)

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    # Validate categories
    unknown = [c for c in cats if c not in CATEGORY_DEFS]
    if unknown:
        print(f"Unknown categories: {', '.join(unknown)}", file=sys.stderr)
        print("Known:", ", ".join(CATEGORY_DEFS.keys()), file=sys.stderr)
        return 2

    print(f"Fetching categories: {', '.join(cats)}")
    features = scrape(args.endpoint, cats, include_social=args.include_social, retries=args.retries)
    print(f"Fetched features: {len(features)}")
    write_geojson(features, args.out)
    print(f"Wrote {args.out}")
    return 0


def hostname(url: str) -> str:
    try:
        host = urlparse(url).netloc
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
