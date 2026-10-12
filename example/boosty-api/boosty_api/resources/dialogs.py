from __future__ import annotations

import json
from typing import Any, Dict, Optional
from pydantic import TypeAdapter

from ..http import BoostyHttp
from ..models.dialogs import DialogDetail, DialogsPage, Message
from ..utils import build_editorjs_text_payload

class DialogsResource:
    def __init__(self, http: BoostyHttp):
        self._http = http

    async def list(self, *, offset: int = 0, auth: bool = True) -> DialogsPage:
        # GET /v1/dialog/ -> {"data":[...], "extra":{...}}
        data = await self._http.request("GET", "/v1/dialog/", params={"offset": offset} if offset else None, auth=auth)
        return TypeAdapter(DialogsPage).validate_python(data)

    async def get(self, dialog_id: int, *, auth: bool = True) -> DialogDetail:
        # GET /v1/dialog/{id}
        data = await self._http.request("GET", f"/v1/dialog/{dialog_id}", auth=auth)
        return TypeAdapter(DialogDetail).validate_python(data)

    async def send_text(self, dialog_id: int, text: str, *, auth: bool = True) -> Message:
        # POST /v1/dialog/{id}/message with form fields:
        # data=<urlencoded JSON list> & teaser_data=[]
        payload = {
            "data": build_editorjs_text_payload(text),
            "teaser_data": "[]",
        }
        # Must be form-encoded (application/x-www-form-urlencoded)
        data = await self._http.request("POST", f"/v1/dialog/{dialog_id}/message", data=payload, auth=auth)
        return TypeAdapter(Message).validate_python(data)
