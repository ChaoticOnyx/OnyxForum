from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Routes:
    """
    Centralized routing table. Some endpoints are not publicly documented and may change.

    Confirmed:
      - get_post: /v1/blog/{blog}/post/{post_id}
    """

    # Posts
    get_post: str = "/v1/blog/{blog}/post/{post_id}"
    list_posts: str = "/v1/blog/{blog}/post"

    # Subscribers / subscriptions
    list_subscribers: str = "/v1/blog/{blog}/subscribers"
    list_subscriptions: str = "/v1/user/subscriptions"

    # Dialogs / messaging
    list_dialogs: str = "/v1/dialogs"
    get_dialog: str = "/v1/dialogs/{dialog_id}"
    send_message: str = "/v1/dialogs/{dialog_id}/messages"
    create_dialog: str = "/v1/dialogs"

    # Donations
    list_donations: str = "/v1/blog/{blog}/donations"

    # Sales
    list_sales: str = "/v1/blog/{blog}/sales"

    # Media / albums
    list_albums: str = "/v1/blog/{blog}/albums"
    get_album: str = "/v1/blog/{blog}/albums/{album_id}"

    # Auth refresh (unofficial; adjust for your actual endpoint)
    refresh_token: str = "/oauth/token"

    def format(self, template: str, **kwargs: str) -> str:
        return template.format(**kwargs)

    def optional(self, template: Optional[str], **kwargs: str) -> Optional[str]:
        return template.format(**kwargs) if template else None
