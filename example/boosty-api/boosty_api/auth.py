from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import BoostyAuthError

DEFAULT_REFRESH_PATH = "/oauth/token"  # required by the user

@dataclass
class BoostyAuth:
    """Authentication container.

    Fields in secrets/boosty_auth.json (minimal):
      - access_token: str
      - refresh_token: str (optional if only public endpoints used)
      - token_type: str (usually 'Bearer', optional)
      - expires_at: int (unix seconds, optional but recommended)

    Optional OAuth client fields (if required by your account/app):
      - client_id, client_secret, redirect_uri, scope
    """
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_at: int = 0

    # Optional OAuth metadata (passed through to refresh if present)
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = ""
    scope: str = ""

    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return int(time.time()) >= int(self.expires_at)

    def will_expire_within(self, seconds: int) -> bool:
        if not self.expires_at:
            return False
        return int(time.time()) + int(seconds) >= int(self.expires_at)

    def to_headers(self) -> Dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"{self.token_type} {self.access_token}"}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BoostyAuth":
        return BoostyAuth(
            access_token=str(d.get("access_token") or ""),
            refresh_token=str(d.get("refresh_token") or ""),
            token_type=str(d.get("token_type") or d.get("tokenType") or "Bearer"),
            expires_at=int(d.get("expires_at") or d.get("expiresAt") or 0),
            client_id=str(d.get("client_id") or d.get("clientId") or ""),
            client_secret=str(d.get("client_secret") or d.get("clientSecret") or ""),
            redirect_uri=str(d.get("redirect_uri") or d.get("redirectUri") or ""),
            scope=str(d.get("scope") or ""),
            raw=dict(d),
        )

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self.raw) if self.raw else {}
        d.update(
            {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_type": self.token_type,
                "expires_at": int(self.expires_at or 0),
            }
        )
        if self.client_id:
            d.setdefault("client_id", self.client_id)
        if self.client_secret:
            d.setdefault("client_secret", self.client_secret)
        if self.redirect_uri:
            d.setdefault("redirect_uri", self.redirect_uri)
        if self.scope:
            d.setdefault("scope", self.scope)
        return d


class BoostyAuthStore:
    """Reads/writes auth JSON to disk."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> BoostyAuth:
        if not self.path.exists():
            raise BoostyAuthError(f"Auth file not found: {self.path}")
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise BoostyAuthError("Auth file must contain a JSON object")
        return BoostyAuth.from_dict(data)

    def save(self, auth: BoostyAuth) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(auth.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
