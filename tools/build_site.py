import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
DATA = ROOT / "data"
PLACES_DIR = WEB / "places"


def load_places() -> List[Dict[str, Any]]:
    places_path = DATA / "places.json"
    if places_path.exists():
        return json.loads(places_path.read_text(encoding="utf-8"))
    # Fallback from GeoJSON
    geo_path = DATA / "friluft.geojson"
    if geo_path.exists():
        geo = json.loads(geo_path.read_text(encoding="utf-8"))
        out = []
        for i, f in enumerate(geo.get("features", [])):
            p = f.get("properties", {})
            [lon, lat] = f.get("geometry", {}).get("coordinates", [None, None])
            out.append({
                "id": p.get("id") or f"feature/{i}",
                "name": p.get("name") or "(namnlös)",
                "categories": p.get("categories", []),
                "lat": lat,
                "lon": lon,
                "website": p.get("link") or p.get("osm_url"),
                "source": {"name": "OSM", "url": p.get("osm_url")},
                "description": None,
                "images": [],
            })
        return out
    raise SystemExit("No places.json or friluft.geojson found. Run ETL or scraper first.")


def slugify(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "plats"


def place_html(place: Dict[str, Any], base_url: str, path: str) -> str:
    title = f"{place.get('name') or 'Plats'} – Friluft"
    desc = (place.get('description') or f"Aktivitet: {', '.join(place.get('categories', [])) or 'friluft'}.")
    url = f"{base_url}/{path}"
    image = (place.get('images') or [None])[0] or "https://via.placeholder.com/1200x630.png?text=Friluft"
    lat = place.get('lat'); lon = place.get('lon')
    cats = ", ".join(place.get('categories', []))
    website = place.get('website') or ''
    ld = {
        "@context": "https://schema.org",
        "@type": "Place",
        "name": place.get('name'),
        "url": url,
        "image": image,
        "description": desc,
        "geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon},
        "sameAs": [website] if website else [],
    }
    # Breadcrumbs
    breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Hem", "item": f"{base_url}/web/"},
            {"@type": "ListItem", "position": 2, "name": place.get('name'), "item": url},
        ],
    }

    return f"""<!doctype html>
<html lang=\"sv\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <meta name=\"description\" content=\"{desc}\" />
  <link rel=\"canonical\" href=\"{url}\" />
  <meta property=\"og:type\" content=\"website\" />
  <meta property=\"og:title\" content=\"{title}\" />
  <meta property=\"og:description\" content=\"{desc}\" />
  <meta property=\"og:url\" content=\"{url}\" />
  <meta property=\"og:image\" content=\"{image}\" />
  <meta name=\"twitter:card\" content=\"summary_large_image\" />
  <script type=\"application/ld+json\">{json.dumps(ld, ensure_ascii=False)}</script>
  <script type=\"application/ld+json\">{json.dumps(breadcrumbs, ensure_ascii=False)}</script>
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap\" rel=\"stylesheet\">
  <style>
    body {{ font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin:0; padding:24px; line-height:1.5; }}
    .wrap {{ max-width: 920px; margin: 0 auto; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; }}
    .meta {{ color:#666; margin-bottom:12px; }}
    a.btn {{ display:inline-block; padding:10px 14px; border-radius:8px; background:#0f766e; color:#fff; text-decoration:none; }}
    a.btn:hover {{ background:#115e59; }}
    .grid {{ display:grid; grid-template-columns: 2fr 1fr; gap:20px; }}
    @media (max-width:900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{ border:1px solid #eee; border-radius:10px; padding:14px; }}
  </style>
  <link rel=\"icon\" href=\"{base_url}/web/favicon.ico\" />
  <meta name=\"robots\" content=\"index,follow\" />
  <meta name=\"theme-color\" content=\"#0f766e\" />
</head>
<body>
  <div class=\"wrap\">
    <p><a href=\"{base_url}/web/\">← Till kartan</a></p>
    <h1>{place.get('name')}</h1>
    <div class=\"meta\">Kategorier: {cats}</div>
    <div class=\"grid\">
      <div class=\"card\">
        <p>{desc}</p>
        <p><strong>Koordinater:</strong> {lat}, {lon}</p>
        {f'<p><a class="btn" href="{website}" rel="nofollow noopener" target="_blank">Besök webbplats</a></p>' if website else ''}
      </div>
      <div class=\"card\">
        <iframe title=\"Karta\" width=\"100%\" height=\"300\" style=\"border:0\" loading=\"lazy\"
          src=\"https://www.openstreetmap.org/export/embed.html?marker={lat}%2C{lon}&layer=mapnik\"></iframe>
      </div>
    </div>
  </div>
</body>
</html>
"""


def generate() -> None:
    base_url = os.environ.get("BASE_URL", "https://perwinroth.github.io/friluft").rstrip("/")
    places = load_places()
    PLACES_DIR.mkdir(parents=True, exist_ok=True)

    index_map = {}
    for p in places:
        sid = p.get('id') or p.get('name') or 'plats'
        slug = slugify(str(sid))
        index_map[p.get('id') or slug] = slug
        rel_path = f"web/places/{slug}.html"
        html = place_html(p, base_url, rel_path)
        (PLACES_DIR / f"{slug}.html").write_text(html, encoding="utf-8")

    # Write index mapping for frontend (optional use)
    (PLACES_DIR / "index.json").write_text(json.dumps(index_map, ensure_ascii=False), encoding="utf-8")

    # Robots.txt and sitemap.xml at repo root (copied by workflow)
    robots = f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n"
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

    # Sitemap
    urls = [
        f"{base_url}/web/",
        f"{base_url}/web/list.html",
        f"{base_url}/web/events/",
    ] + [f"{base_url}/web/places/{slugify(str(p.get('id') or p.get('name')))}.html" for p in places]
    parts = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for u in urls:
        parts.append(f"  <url><loc>{u}</loc></url>")
    parts.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    generate()
