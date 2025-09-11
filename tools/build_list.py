import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "friluft.geojson"
OUT = ROOT / "web" / "list.html"


def load_items(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        geo = json.load(f)
    items = []
    for ftr in geo.get("features", []):
        p = ftr.get("properties", {})
        g = ftr.get("geometry", {})
        if g.get("type") != "Point":
            continue
        coords = g.get("coordinates", [None, None])
        lng, lat = coords
        items.append({
            "id": p.get("id"),
            "name": p.get("name") or "(namnlös)",
            "link": p.get("link") or p.get("osm_url"),
            "cats": p.get("categories", []),
            "lat": lat,
            "lng": lng,
        })
    items.sort(key=lambda x: (x["name"].lower(), x["id"]))
    return items


HTML_HEAD = """<!DOCTYPE html>
<html lang=\"sv\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Friluft – Lista</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin:0; }
    header { position: sticky; top:0; background:#fff; padding:12px; border-bottom:1px solid #eee; z-index:10; }
    .wrap { max-width: 1100px; margin: 0 auto; padding: 0 12px; }
    h1 { font-size: 20px; margin: 0 0 8px 0; }
    .toolbar { display:flex; gap:8px; flex-wrap: wrap; align-items:center; }
    input[type=text] { padding:8px; border:1px solid #ddd; border-radius:6px; width: 260px; }
    .badge { display:inline-block; padding:1px 6px; border-radius:10px; font-size:11px; color:#fff; margin-right:4px; }
    .count { color:#666; font-size:13px; margin-left: auto; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:10px; padding:12px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .item { border:1px solid #eee; border-radius:8px; padding:10px; }
    .item .name { font-weight:600; margin-bottom:4px; }
    .item .meta { color:#666; font-size:12px; display:flex; gap:8px; align-items: center; }
    .item .meta a { color:#0645ad; text-decoration:none; }
    .item .meta a:hover { text-decoration: underline; }
    .cats { display:inline-flex; gap:4px; flex-wrap: wrap; }
  </style>
</head>
<body>
  <header>
    <div class=\"wrap\">
      <h1>Friluft – Lista</h1>
      <div class=\"toolbar\">
        <input id=\"q\" type=\"text\" placeholder=\"Sök namn...\" />
        <span class=\"count\" id=\"count\"></span>
      </div>
    </div>
  </header>
  <main class=\"wrap\">
    <div class=\"grid\" id=\"list\"></div>
  </main>
  <script>
    const COLORS = {"national_park":"#2ca25f","nature_reserve":"#99d8c9","camp_site":"#fb6a4a","shelter":"#ef3b2c","viewpoint":"#8856a7","picnic_site":"#9ebcda","slipway":"#3182bd","canoe_kayak":"#41b6c4","boat_rental":"#0868ac"};
    const LABELS = {"national_park":"Nationalpark","nature_reserve":"Naturreservat","camp_site":"Camping","shelter":"Vindskydd / Shelter","viewpoint":"Utsiktsplats","picnic_site":"Picknick","slipway":"Båtramp / Slip","canoe_kayak":"Kanot / Kajak","boat_rental":"Båt/Kanot-uthyrning"};
    const ITEMS = 
"""

HTML_TAIL = """
;
    const q = document.getElementById('q');
    const list = document.getElementById('list');
    const count = document.getElementById('count');

    function render(filter="") {
      const f = filter.trim().toLowerCase();
      const items = f ? ITEMS.filter(it => it.name.toLowerCase().includes(f)) : ITEMS;
      count.textContent = `${items.length} platser`;
      const parts = [];
      for (const it of items) {
        const cats = (it.cats||[]).map(c=>`<span class=\"badge\" style=\"background:${COLORS[c]||'#444'}\">${LABELS[c]||c}</span>`).join(' ');
        const link = it.link ? `<a href=\"${it.link}\" target=\"_blank\" rel=\"noopener\">Länk</a>` : '';
        parts.push(`
          <div class=\"item\">
            <div class=\"name\">${it.name}</div>
            <div class=\"meta\">
              <span class=\"cats\">${cats}</span>
              <span>${it.lat?.toFixed(5)||''}, ${it.lng?.toFixed(5)||''}</span>
              ${link}
            </div>
          </div>
        `);
      }
      list.innerHTML = parts.join('\n');
    }
    q.addEventListener('input', () => render(q.value));
    render('');
  </script>
</body>
</html>
"""


def main():
    if not DATA.exists():
        raise SystemExit(f"Missing data file: {DATA}")
    items = load_items(DATA)
    # Only keep necessary fields to keep size down
    slim = [{
        "id": it["id"],
        "name": it["name"],
        "link": it["link"],
        "cats": it["cats"],
        "lat": it["lat"],
        "lng": it["lng"],
    } for it in items]
    json_blob = json.dumps(slim, ensure_ascii=False)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HTML_HEAD)
        f.write(json_blob)
        f.write(HTML_TAIL)
    print(f"Wrote {OUT} with {len(items)} items.")


if __name__ == "__main__":
    main()
