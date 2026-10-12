"""Boosty API client (unofficial).

Features:
- Posts (get + best-effort list)
- Subscribers
- Dialogs (list, get, send text)
- Donations / Sales (donation sales)
- Blog stats (current, metrics, stat/data, events)
- Auto token refresh via refresh_token + retry on 401
- Media helpers (download URLs, parse media from posts)
"""

from .client import BoostyApi
from .auth import BoostyAuth, BoostyAuthStore
from .exceptions import BoostyApiError, BoostyAuthError

__all__ = ["BoostyApi", "BoostyAuth", "BoostyAuthStore", "BoostyApiError", "BoostyAuthError"]
