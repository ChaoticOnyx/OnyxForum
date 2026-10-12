from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import httpx

from .auth import BoostyAuth, DEFAULT_REFRESH_PATH
from .exceptions import BoostyApiError, BoostyAuthError

class BoostyHttp:
    def __init__(
        self,
        base_url: str,
        auth: BoostyAuth | None = None,
        timeout: float = 30.0,
        refresh_path: str = DEFAULT_REFRESH_PATH,
        user_agent: str = "boosty-api-python/1.0",
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = auth or BoostyAuth()
        self.timeout = timeout
        self.refresh_path = refresh_path
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": user_agent, "Accept": "application/json, text/plain, */*"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def refresh_token(self) -> None:
        if not self.auth.refresh_token:
            raise BoostyAuthError("No refresh_token in auth. Cannot refresh.")

        # OAuth refresh is done via POST /oauth/token with form payload
        url = self.refresh_path if self.refresh_path.startswith("/") else "/" + self.refresh_path
        form: Dict[str, Any] = {
            "grant_type": "refresh_token",
            "refresh_token": self.auth.refresh_token,
        }
        # Some installations require client_id / client_secret
        if self.auth.client_id:
            form["client_id"] = self.auth.client_id
        if self.auth.client_secret:
            form["client_secret"] = self.auth.client_secret
        if self.auth.redirect_uri:
            form["redirect_uri"] = self.auth.redirect_uri
        if self.auth.scope:
            form["scope"] = self.auth.scope

        resp = await self._client.post(url, data=form, headers={"Accept": "application/json"})
        if resp.status_code >= 400:
            raise BoostyAuthError(
                "Failed to refresh token",
                status_code=resp.status_code,
                payload=_safe_json(resp),
                url=str(resp.request.url),
            )
        data = _safe_json(resp)
        if not isinstance(data, dict) or not data.get("access_token"):
            raise BoostyAuthError("Refresh response does not contain access_token", payload=data, url=str(resp.request.url))

        self.auth.access_token = str(data.get("access_token"))
        if data.get("refresh_token"):
            self.auth.refresh_token = str(data.get("refresh_token"))
        self.auth.token_type = str(data.get("token_type") or data.get("tokenType") or self.auth.token_type or "Bearer")

        # expires_in (seconds) is typical
        expires_in = data.get("expires_in") or data.get("expiresIn")
        if expires_in is not None:
            try:
                self.auth.expires_at = int(time.time()) + int(expires_in)
            except Exception:
                pass

        # keep raw for persistence
        try:
            self.auth.raw = dict(self.auth.raw or {})
            self.auth.raw.update(data)
        except Exception:
            pass

    async def request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        params: Dict[str, Any] | None = None,
        json_body: Any = None,
        data: Any = None,
        headers: Dict[str, str] | None = None,
        retry_on_401: bool = True,
    ) -> Any:
        hdrs = dict(headers or {})
        if auth and self.auth.access_token:
            # proactive refresh if close to expiry
            if self.auth.will_expire_within(30) and self.auth.refresh_token:
                await self.refresh_token()
            hdrs.update(self.auth.to_headers())

        resp = await self._client.request(method, path, params=params, json=json_body, data=data, headers=hdrs)

        if resp.status_code == 401 and auth and retry_on_401 and self.auth.refresh_token:
            await self.refresh_token()
            hdrs.update(self.auth.to_headers())
            resp = await self._client.request(method, path, params=params, json=json_body, data=data, headers=hdrs)

        if resp.status_code >= 400:
            raise BoostyApiError(
                f"HTTP error calling {method.upper()} {path}",
                status_code=resp.status_code,
                payload=_safe_json(resp),
                url=str(resp.request.url),
            )

        # Some endpoints return empty body
        if not resp.content:
            return None
        ct = resp.headers.get("content-type", "")
        if "application/json" in ct or "text/json" in ct:
            return _safe_json(resp)
        # fallback: try json anyway
        try:
            return resp.json()
        except Exception:
            return resp.text

def _safe_json(resp: httpx.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        try:
            return {"text": resp.text}
        except Exception:
            return None
