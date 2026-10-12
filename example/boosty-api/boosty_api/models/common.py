from __future__ import annotations
from typing import Optional, Union
from pydantic import BaseModel, Field

UserId = Union[int, str]

class User(BaseModel):
    id: UserId
    name: Optional[str] = None
    email: Optional[str] = None
    avatarUrl: Optional[str] = None
    hasAvatar: Optional[bool] = None
    isOfficial: Optional[bool] = None
    isBlogger: Optional[bool] = None
    url: Optional[str] = None

class Extra(BaseModel):
    total: int | None = None
    offset: int | str | None = None
    isLast: bool | None = None
    isFirst: bool | None = None
