from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from .common import User

class PostMedia(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    rendition: Optional[str] = None

class Post(BaseModel):
    id: str
    title: Optional[str] = None
    createdAt: Optional[int] = None
    user: Optional[User] = None

    # Boosty returns many fields; keep them as raw too
    raw: Dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if "raw" not in self.__dict__ or not self.__dict__["raw"]:
            # store unknown keys for easier debugging
            self.raw = {k: v for k, v in self.__pydantic_extra__.items()} if getattr(self, "__pydantic_extra__", None) else {}

    def media_urls(self) -> List[str]:
        urls: List[str] = []
        # common patterns in Boosty posts:
        # - "teaser" / "data" blocks include images with 'url'
        # - "media" or "images" arrays
        def walk(obj: Any) -> None:
            if isinstance(obj, dict):
                if obj.get("type") in ("image", "video", "audio", "file") and isinstance(obj.get("url"), str):
                    urls.append(obj["url"])
                if isinstance(obj.get("url"), str) and "images.boosty.to" in obj["url"]:
                    urls.append(obj["url"])
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)
        walk(self.raw)
        # de-dup preserve order
        seen = set()
        out = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        return out
