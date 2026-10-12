from __future__ import annotations

from typing import Any, Optional

from pydantic import TypeAdapter

from ..client import BoostyClient
from ..models import Donation
from ..pagination import Page


class DonationsResource:
    def __init__(self, api: BoostyClient) -> None:
        self.api = api

    async def list(
        self,
        blog: str,
        *,
        limit: int = 50,
        offset: int = 0,
        auth: bool = True,
        extra_params: Optional[dict[str, Any]] = None,
    ) -> Page:
        path = self.api.routes.format(self.api.routes.list_donations, blog=blog)
        params = {"limit": limit, "offset": offset}
        if extra_params:
            params.update(extra_params)

        data = await self.api.request("GET", path, params=params, require_auth=auth)
        items_raw = data.get("items") or data.get("data") or []
        items = [
            TypeAdapter(Donation).validate_python({"raw": x, **(x or {}), "id": str((x or {}).get("id"))})
            for x in items_raw
        ]
        next_offset = data.get("nextOffset")
        if next_offset is None and len(items_raw) == limit:
            next_offset = offset + limit
        return Page(items=items, next_offset=next_offset)
