from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator



class User(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def _id_to_str(cls, v: Any) -> Any:
        if v is None:
            return None
        # Boosty иногда отдаёт int
        return str(v)


class Post(BaseModel):
    id: str
    title: Optional[str] = None
    createdAt: Optional[int] = None
    publishTime: Optional[int] = None
    updatedAt: Optional[int] = None
    hasAccess: Optional[bool] = None
    user: Optional[User] = None
    tags: list[dict[str, Any]] = Field(default_factory=list)
    data: list[dict[str, Any]] = Field(default_factory=list)  # raw blocks

    @field_validator("id", mode="before")
    @classmethod
    def _post_id_to_str(cls, v: Any) -> Any:
        return str(v)
        
    def iter_media_urls(self) -> list[str]:
        """
        Heuristic media URL extraction from common block shapes.
        """
        urls: list[str] = []
        for item in self.data or []:
            t = (item or {}).get("type")
            if t in ("image", "file", "audio", "video"):
                u = (item or {}).get("url")
                if isinstance(u, str) and u:
                    urls.append(u)
            if t == "ok_video":
                pus = (item or {}).get("playerUrls") or []
                for pu in pus:
                    u = (pu or {}).get("url")
                    if isinstance(u, str) and u:
                        urls.append(u)
        return urls


class Dialog(BaseModel):
    id: str
    title: Optional[str] = None
    lastMessageAt: Optional[int] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    id: Optional[str] = None
    text: Optional[str] = None
    createdAt: Optional[int] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Donation(BaseModel):
    id: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    createdAt: Optional[int] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class Sale(BaseModel):
    id: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    createdAt: Optional[int] = None
    raw: dict[str, Any] = Field(default_factory=dict)
