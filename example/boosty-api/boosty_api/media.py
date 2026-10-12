from __future__ import annotations

from pathlib import Path
from typing import Optional

import httpx


async def download_file(
    client: httpx.AsyncClient,
    url: str,
    dest_path: str | Path,
    *,
    chunk_size: int = 1024 * 512,
    timeout: Optional[float] = None,
) -> Path:
    """
    Downloads a file from a direct media URL (often CDN).
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    async with client.stream("GET", url, timeout=timeout) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            async for chunk in r.aiter_bytes(chunk_size=chunk_size):
                f.write(chunk)
    return dest
