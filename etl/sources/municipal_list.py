from typing import List, Dict, Any
import csv
import io
import json
import requests
from pathlib import Path


def fetch_municipal_list(url: str) -> List[Dict[str, Any]]:
    """Fetch a list of Swedish municipalities with optional websites.

    Expected formats:
    - CSV with columns: name, website (optional), county (optional)
    - JSON array of objects with keys: name, website
    """
    if not url:
        return []
    content: bytes
    # Support local file paths in repo or file:// URLs
    if url.startswith('file://'):
        try:
            content = Path(url[7:]).read_bytes()
        except Exception:
            return []
    elif url.startswith('http://') or url.startswith('https://'):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            content = r.content
        except Exception:
            return []
    else:
        # Treat as relative/absolute file path
        try:
            content = Path(url).read_bytes()
        except Exception:
            return []

    # Try JSON first
    try:
        data = json.loads(content.decode('utf-8', errors='replace'))
        out: List[Dict[str, Any]] = []
        if isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and it.get('name'):
                    out.append({'name': it['name'], 'website': it.get('website')})
        return out
    except Exception:
        pass

    # CSV
    try:
        text = content.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
        out: List[Dict[str, Any]] = []
        for row in reader:
            name = row.get('name') or row.get('namn')
            if not name:
                continue
            out.append({'name': name, 'website': row.get('website') or row.get('webb')})
        return out
    except Exception:
        return []
