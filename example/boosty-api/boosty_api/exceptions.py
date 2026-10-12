from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class BoostyApiError(Exception):
    message: str
    status_code: Optional[int] = None
    payload: Any = None
    url: str | None = None

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.url:
            parts.append(f"url={self.url}")
        return "BoostyApiError(" + ", ".join(parts) + ")"

@dataclass
class BoostyAuthError(BoostyApiError):
    pass
