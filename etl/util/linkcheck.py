import asyncio
import time
from typing import List, Dict, Any

import aiohttp


async def _check_one(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Dict[str, Any]:
    out: Dict[str, Any] = {"url": url, "ok": False, "status": None, "final": None}
    try:
        async with session.head(url, allow_redirects=True, timeout=timeout) as resp:
            out["status"] = resp.status
            out["final"] = str(resp.url)
            if 200 <= resp.status < 400:
                out["ok"] = True
                return out
    except Exception:
        pass
    # Try GET as fallback
    try:
        async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
            out["status"] = resp.status
            out["final"] = str(resp.url)
            out["ok"] = 200 <= resp.status < 400
            return out
    except Exception:
        return out


async def _run(urls: List[str], concurrency: int = 10) -> List[Dict[str, Any]]:
    connector = aiohttp.TCPConnector(limit=concurrency)
    headers = {"User-Agent": "FriluftLinkCheck/0.1 (+https://github.com/perwinroth/friluft)"}
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [asyncio.create_task(_check_one(session, u)) for u in urls]
        return await asyncio.gather(*tasks)


def check_links(urls: List[str], concurrency: int = 10) -> List[Dict[str, Any]]:
    if not urls:
        return []
    return asyncio.run(_run(urls, concurrency=concurrency))

