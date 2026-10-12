from __future__ import annotations
from pydantic import TypeAdapter

from ..http import BoostyHttp
from ..models.sales import DonationSalesResponse

class SalesResource:
    def __init__(self, http: BoostyHttp):
        self._http = http

    async def donations(self, blog: str, *, limit: int = 20, offset: int = 0, auth: bool = True) -> DonationSalesResponse:
        # GET /v1/blog/{blog}/sales/donation/  (note trailing slash in capture)
        params = {"limit": limit, "offset": offset} if (limit or offset) else None
        data = await self._http.request("GET", f"/v1/blog/{blog}/sales/donation/", params=params, auth=auth)
        return TypeAdapter(DonationSalesResponse).validate_python(data)
