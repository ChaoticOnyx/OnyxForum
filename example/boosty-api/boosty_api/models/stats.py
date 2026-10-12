from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .common import Extra, User

class BlogStatCurrent(BaseModel):
    balance: float | int | None = None
    payoutSum: float | int | None = None
    paidCount: int | None = None
    hold: float | int | None = None
    followersCount: int | None = None
    income: float | int | None = None

class BlogStatMetrics(BaseModel):
    incSubscribers: int | None = None
    incFollowers: int | None = None
    incSubscribersMoney: float | int | None = None
    referalMoneyOut: float | int | None = None
    recurrents: int | None = None
    referal: int | None = None
    referalMoney: float | int | None = None
    messagesSale: int | None = None
    donationsMoney: float | int | None = None
    messagesSaleMoney: float | int | None = None
    giftsSale: int | None = None
    postsSale: int | None = None
    totalMoney: float | int | None = None
    upSubscribersMoney: float | int | None = None
    recurrentsMoney: float | int | None = None
    holds: float | int | None = None
    donations: int | None = None
    decSubscribers: int | None = None
    decFollowers: int | None = None
    postSaleMoney: float | int | None = None
    giftsSaleMoney: float | int | None = None
    upSubscribers: int | None = None

class DayPoint(BaseModel):
    year: int
    month: int
    day: int
    count: float | int

class BlogStatData(BaseModel):
    # Many arrays, keep as dict[str, list[DayPoint]]
    raw: Dict[str, list[DayPoint]] = Field(default_factory=dict)

    @staticmethod
    def from_api(payload: Dict[str, Any]) -> "BlogStatData":
        parsed: Dict[str, list[DayPoint]] = {}
        for k, v in payload.items():
            if isinstance(v, list):
                pts = []
                for it in v:
                    if isinstance(it, dict) and {"year","month","day","count"}.issubset(it.keys()):
                        pts.append(DayPoint(**it))
                parsed[k] = pts
        return BlogStatData(raw=parsed)

class StatEvent(BaseModel):
    eventType: str | None = None
    switchType: str | None = None
    createdAt: int | None = None
    bloggerId: int | None = None
    amount: float | int | None = None
    isFeePaid: bool | None = None
    user: User | None = None
    levelId: int | None = None
    period: int | None = None
    isRestore: bool | None = None
    isSuspended: bool | None = None
    payoutSystem: str | None = None
    destination: str | None = None

class StatEventsPage(BaseModel):
    extra: Extra | None = None
    data: list[StatEvent] = Field(default_factory=list)
