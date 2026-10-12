from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .common import User, Extra

class Level(BaseModel):
    id: int | None = None
    name: str | None = None
    price: float | int | None = None
    currencyPrices: Dict[str, float | int] | None = None
    deleted: bool | None = None
    ownerId: int | None = None
    isLimited: bool | None = None
    createdAt: int | None = None
    isArchived: bool | None = None
    isHidden: bool | None = None
    data: list[Any] | None = None

class Subscriber(BaseModel):
    id: int
    name: str | None = None
    email: str | None = None
    avatarUrl: str | None = None
    hasAvatar: bool | None = None
    isOfficial: bool | None = None
    canWrite: bool | None = None
    subscribed: bool | None = None
    isFeePaid: bool | None = None
    status: str | None = None
    price: float | int | None = None
    payments: float | int | None = None
    onTime: int | None = None
    offTime: int | None = None
    level: Level | None = None

class SubscribersPage(BaseModel):
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    data: List[Subscriber] = Field(default_factory=list)
