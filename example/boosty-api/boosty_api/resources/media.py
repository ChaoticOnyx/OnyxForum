from __future__ import annotations

from pathlib import Path
from typing import Optional

import httpx

from ..exceptions import BoostyApiError

class MediaResource:
    def __init__(self, timeout: float = 60.0, user_agent: str = "boosty-api-python/1.0"):
        self._client = httpx.AsyncClient(timeout=timeout, headers={"User-Agent": user_agent})

    async def aclose(self) -> None:
        await self._client.aclose()

    async def download(self, url: str, dest: str | Path) -> Path:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        resp = await self._client.get(url, follow_redirects=True)
        if resp.status_code >= 400:
            raise BoostyApiError(f"Failed to download media: {url}", status_code=resp.status_code, payload={"text": resp.text})
        dest.write_bytes(resp.content)
        return dest
