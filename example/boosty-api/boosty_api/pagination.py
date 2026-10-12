from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Optional


@dataclass
class Page:
    items: list[Any]
    next_offset: Optional[int] = None


async def paginate(
    fetch_page: Callable[[int], "Page"],
    start_offset: int = 0,
    limit: Optional[int] = None,
) -> AsyncIterator[Any]:
    emitted = 0
    offset = start_offset
    while True:
        page = await fetch_page(offset)
        for it in page.items:
            yield it
            emitted += 1
            if limit is not None and emitted >= limit:
                return
        if page.next_offset is None:
            return
        offset = page.next_offset
