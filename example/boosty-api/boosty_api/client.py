from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .auth import BoostyAuth, BoostyAuthStore
from .http import BoostyHttp
from .resources.posts import PostsResource
from .resources.subscribers import SubscribersResource
from .resources.dialogs import DialogsResource
from .resources.stats import StatsResource
from .resources.sales import SalesResource
from .resources.media import MediaResource

DEFAULT_BASE_URL = "https://api.boosty.to"

class BoostyApi:
    """Async Boosty API client."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        auth: BoostyAuth | None = None,
        auth_store: BoostyAuthStore | None = None,
        timeout: float = 30.0,
        refresh_path: str = "/oauth/token",
        user_agent: str = "boosty-api-python/1.0",
    ):
        self.auth_store = auth_store
        self.http = BoostyHttp(
            base_url=base_url,
            auth=auth,
            timeout=timeout,
            refresh_path=refresh_path,
            user_agent=user_agent,
        )

        self.posts = PostsResource(self.http)
        self.subscribers = SubscribersResource(self.http)
        self.dialogs = DialogsResource(self.http)
        self.stats = StatsResource(self.http)
        self.sales = SalesResource(self.http)

        self.media = MediaResource(timeout=max(timeout, 60.0), user_agent=user_agent)

    @property
    def auth(self) -> BoostyAuth:
        return self.http.auth

    async def refresh(self) -> None:
        await self.http.refresh_token()
        if self.auth_store:
            self.auth_store.save(self.auth)

    async def aclose(self) -> None:
        try:
            if self.auth_store:
                self.auth_store.save(self.auth)
        finally:
            await self.http.aclose()
            await self.media.aclose()

    async def __aenter__(self) -> "BoostyApi":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()
