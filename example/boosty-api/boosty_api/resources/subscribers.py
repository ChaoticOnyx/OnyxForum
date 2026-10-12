from __future__ import annotations
from pydantic import TypeAdapter

from ..http import BoostyHttp
from ..models.subscribers import SubscribersPage

class SubscribersResource:
    def __init__(self, http: BoostyHttp):
        self._http = http

    async def list(self, blog: str, *, limit: int = 20, offset: int = 0, auth: bool = True) -> SubscribersPage:
        # GET /v1/blog/{blog}/subscribers  (limit, offset)
        data = await self._http.request("GET", f"/v1/blog/{blog}/subscribers", params={"limit": limit, "offset": offset}, auth=auth)
        return TypeAdapter(SubscribersPage).validate_python(data)
