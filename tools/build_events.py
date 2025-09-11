import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'events.json'
OUT = ROOT / 'web' / 'events' / 'index.html'


def build():
    events = []
    if DATA.exists():
        events = json.loads(DATA.read_text(encoding='utf-8'))
    events.sort(key=lambda e: e.get('date') or '')
    # JSON-LD Event collection
    items = []
    for ev in events:
        ld = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": ev.get('name'),
            "startDate": ev.get('date'),
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "location": {
                "@type": "Place",
                "name": ev.get('location'),
                "address": ev.get('location')
            },
            "description": ev.get('description'),
            "url": ev.get('registrationUrl') or ''
        }
        items.append(ld)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Build HTML list separately to avoid f-string backslash issues
    list_parts = []
    for ev in events:
        url = ev.get('registrationUrl') or ''
        link_html = f'<a class="btn" href="{url}" target="_blank" rel="noopener">Anmälan</a>' if url else ''
        list_parts.append(
            f"<li><strong>{ev.get('name')}</strong><br/><small>{ev.get('date')} – {ev.get('location')}</small><br/>{link_html}</li>"
        )

    html = f"""<!doctype html>
<html lang=\"sv\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Friluft – Evenemang</title>
  <meta name=\"description\" content=\"Kalender med lopp och evenemang inom friluftsliv i Sverige.\" />
  <link rel=\"canonical\" href=\"https://perwinroth.github.io/friluft/web/events/\" />
  <meta property=\"og:type\" content=\"website\" />
  <meta property=\"og:title\" content=\"Friluft – Evenemang\" />
  <meta property=\"og:description\" content=\"Upptäck lopp och evenemang.\" />
  <meta property=\"og:url\" content=\"https://perwinroth.github.io/friluft/web/events/\" />
  <meta property=\"og:image\" content=\"https://via.placeholder.com/1200x630.png?text=Friluft\" />
  <meta name=\"twitter:card\" content=\"summary_large_image\" />
  <script type=\"application/ld+json\">{{"@context":"https://schema.org","@type":"ItemList","itemListElement":{json.dumps(items, ensure_ascii=False)}}}</script>
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap\" rel=\"stylesheet\">
  <style>
    body {{ font-family: 'Inter', system-ui, sans-serif; margin:0; padding:24px; }}
    .wrap {{ max-width: 920px; margin: 0 auto; }}
    h1 {{ margin: 0 0 12px; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ border:1px solid #eee; border-radius:10px; padding:12px; margin-bottom:8px; }}
    a.btn {{ display:inline-block; padding:8px 12px; border-radius:8px; background:#0f766e; color:#fff; text-decoration:none; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <p><a href=\"../\">← Till kartan</a></p>
    <h1>Evenemang</h1>
    <ul>
      {''.join(list_parts)}
    </ul>
  </div>
</body>
</html>
"""
    OUT.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    build()
