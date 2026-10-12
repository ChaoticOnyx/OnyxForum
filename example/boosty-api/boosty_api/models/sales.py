from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
from .common import Extra, User

class DonationSale(BaseModel):
    id: int
    amount: float | int | None = None
    createdAt: int | None = None
    targetId: int | None = None
    type: str | None = None
    bloggerId: int | None = None
    isFeePaid: bool | None = None
    user: User | None = None

class DonationsSalesData(BaseModel):
    donationsSales: List[DonationSale] = Field(default_factory=list)

class DonationSalesResponse(BaseModel):
    data: DonationsSalesData | None = None
    extra: Extra | None = None
