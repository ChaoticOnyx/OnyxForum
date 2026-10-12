from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import TypeAdapter

from ..http import BoostyHttp
from ..models.stats import BlogStatCurrent, BlogStatMetrics, BlogStatData, StatEventsPage

class StatsResource:
    def __init__(self, http: BoostyHttp):
        self._http = http

    async def current(self, blog: str, *, auth: bool = True) -> BlogStatCurrent:
        data = await self._http.request("GET", f"/v1/blog/stat/{blog}/current", auth=auth)
        return TypeAdapter(BlogStatCurrent).validate_python(data)

    async def metrics(self, blog: str, *, auth: bool = True) -> BlogStatMetrics:
        data = await self._http.request("GET", f"/v1/blog/stat/{blog}/metrics", auth=auth)
        return TypeAdapter(BlogStatMetrics).validate_python(data)

    async def data(self, blog: str, *, auth: bool = True) -> BlogStatData:
        payload = await self._http.request("GET", f"/v1/blog/{blog}/stat/data", auth=auth)
        if isinstance(payload, dict):
            return BlogStatData.from_api(payload)
        return BlogStatData()

    async def events(self, blog: str, *, offset: int = 0, auth: bool = True) -> StatEventsPage:
        params = {"offset": offset} if offset else None
        data = await self._http.request("GET", f"/v1/blog/stat/{blog}/events", params=params, auth=auth)
        return TypeAdapter(StatEventsPage).validate_python(data)
