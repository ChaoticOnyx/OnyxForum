from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .common import User, Extra

class Attachments(BaseModel):
    class Item(BaseModel):
        count: int | None = None
        previewUrl: str | None = None
    files: Item | None = None
    audios: Item | None = None
    images: Item | None = None
    text: Item | None = None
    videos: Item | None = None

class Donation(BaseModel):
    createdAt: int | None = None
    amount: float | int | None = None
    type: str | None = None
    id: int | None = None
    bloggerId: int | None = None
    user: User | None = None
    isFeePaid: bool | None = None
    targetId: int | None = None

class Message(BaseModel):
    id: int
    dialogId: int
    authorId: int | None = None
    createdAt: int | None = None
    previewType: str | None = None
    price: float | int | None = None
    currencyPrices: Dict[str, float | int] | None = None
    isPaid: bool | None = None
    isFeePaid: bool | None = None
    isDeleted: bool | None = None
    isRead: bool | None = None
    payWall: bool | None = None
    teaser: list[Any] | None = None
    data: list[Any] | None = None
    attachments: Attachments | None = None
    donation: Donation | None = None

class DialogListItem(BaseModel):
    id: int
    createdAt: int | None = None
    unreadMsgCount: int | None = None
    chatmate: User | None = None
    lastMessage: Message | None = None

class DialogsPage(BaseModel):
    data: List[DialogListItem] = Field(default_factory=list)
    extra: Extra | None = None

class MessagesBlock(BaseModel):
    extra: Extra | None = None
    data: List[Message] = Field(default_factory=list)

class Relation(BaseModel):
    type: str | None = None
    canWrite: bool | None = None
    canWriteMe: bool | None = None
    needDonation: bool | None = None
    isBlackListed: bool | None = None
    isChatmateBlackListed: bool | None = None
    startAt: int | None = None
    chatmateRequiresVerificationForPayments: bool | None = None

class DialogDetail(BaseModel):
    id: int
    createdAt: int | None = None
    signedQuery: str | None = None
    unreadMsgCount: int | None = None
    wsChannel: str | None = None
    chatmate: User | None = None
    relation: Relation | None = None
    messages: MessagesBlock | None = None
