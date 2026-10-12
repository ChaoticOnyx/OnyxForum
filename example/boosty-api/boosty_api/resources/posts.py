from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import TypeAdapter

from ..http import BoostyHttp
from ..models.posts import Post

class PostsResource:
    def __init__(self, http: BoostyHttp):
        self._http = http

    async def get(self, blog: str, post_id: str, *, auth: bool = False) -> Post:
        # Known working unauth endpoint pattern in user's tests:
        # GET /v1/blog/{blog}/post/{post_id}
        data = await self._http.request("GET", f"/v1/blog/{blog}/post/{post_id}", auth=auth)
        return TypeAdapter(Post).validate_python(data)

    async def list(self, blog: str, *, limit: int = 10, offset: int = 0, auth: bool = False) -> Any:
        """Best-effort list. Boosty has multiple variants; we try a few."""
        candidates = [
            ("/v1/blog/{blog}/post/", {"limit": limit})
        ]
        last_exc: Exception | None = None
        for path_t, params in candidates:
            try:
                return await self._http.request("GET", path_t.format(blog=blog), params=params, auth=auth)
            except Exception as e:
                last_exc = e
        if last_exc:
            raise last_exc
        return None
