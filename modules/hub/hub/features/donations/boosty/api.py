import json
import hashlib
import logging
import os
import time
from decimal import Decimal
from pathlib import Path

import requests


logger = logging.getLogger("donations.boosty.api")


def event_external_id(payload):
    """Build a stable ID for stat events, which do not expose an API ID."""
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return "event:{}".format(digest)


def next_page_offset(current_offset, item_count, extra, requested_limit):
    """Return Boosty's next offset, or ``None`` at a verified page end.

    Boosty may cap a response below the requested limit.  Therefore a short
    page is not an end-of-history signal when ``extra.offset``/``total`` says
    that more data exists.
    """
    extra = extra or {}
    if extra.get("isLast") is True or item_count <= 0:
        return None

    next_offset = extra.get("offset")
    if next_offset not in (None, current_offset, str(current_offset)):
        try:
            total = int(extra.get("total"))
            if total > 0 and int(next_offset) >= total:
                return None
        except (TypeError, ValueError):
            pass
        return next_offset

    try:
        fallback = int(current_offset) + int(item_count)
    except (TypeError, ValueError):
        fallback = None

    try:
        total = int(extra.get("total"))
    except (TypeError, ValueError):
        total = None
    if total is not None and total > 0:
        return fallback if fallback is not None and fallback < total else None
    if item_count < requested_limit:
        return None
    return fallback


class BoostyApiError(RuntimeError):
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BoostyApiClient:
    """Small synchronous client for the endpoints present in the reference.

    APScheduler invokes the integration from a regular worker thread, so using
    the project's existing ``requests`` dependency avoids introducing a second
    async runtime. Refreshed OAuth tokens are persisted in the configured,
    git-ignored state file.
    """

    def __init__(self, config):
        self.base_url = str(config.get("BOOSTY_API_BASE_URL") or "").rstrip("/")
        self.blog = str(config.get("BOOSTY_BLOG_NAME") or "")
        self.timeout = float(config.get("BOOSTY_API_TIMEOUT_SECONDS", 30))
        self.retries = int(config.get("BOOSTY_API_RETRY_COUNT", 3))
        self.backoff = float(config.get("BOOSTY_API_RETRY_BACKOFF_SECONDS", 1))
        self.max_backoff = float(config.get("BOOSTY_API_MAX_BACKOFF_SECONDS", 30))
        self.refresh_path = str(config.get("BOOSTY_OAUTH_REFRESH_PATH", "/oauth/token"))
        self.user_agent = str(config.get("BOOSTY_API_USER_AGENT", "onyx-forum-boosty/1.0"))
        self.state_path = config.get("BOOSTY_AUTH_STATE_PATH")
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "User-Agent": self.user_agent,
        })
        self.auth = {
            "access_token": str(config.get("BOOSTY_ACCESS_TOKEN") or ""),
            "refresh_token": str(config.get("BOOSTY_REFRESH_TOKEN") or ""),
            "token_type": str(config.get("BOOSTY_TOKEN_TYPE") or "Bearer"),
            "expires_at": int(config.get("BOOSTY_TOKEN_EXPIRES_AT") or 0),
            "client_id": str(config.get("BOOSTY_CLIENT_ID") or ""),
            "client_secret": str(config.get("BOOSTY_CLIENT_SECRET") or ""),
            "redirect_uri": str(config.get("BOOSTY_REDIRECT_URI") or ""),
            "scope": str(config.get("BOOSTY_SCOPE") or ""),
        }
        self._load_auth_state()
        if not self.base_url:
            raise BoostyApiError("BOOSTY_API_BASE_URL is not configured")
        if not self.blog:
            raise BoostyApiError("BOOSTY_BLOG_NAME is not configured")

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()

    def _load_auth_state(self):
        if not self.state_path:
            return
        path = Path(self.state_path)
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                for key in self.auth:
                    if payload.get(key) not in (None, ""):
                        self.auth[key] = payload[key]
        except (OSError, ValueError):
            logger.exception("Failed to load Boosty OAuth state from %s", path)

    def _save_auth_state(self):
        if not self.state_path:
            return
        path = Path(self.state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.auth, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(str(temporary), 0o600)
        except OSError:
            pass
        os.replace(str(temporary), str(path))

    def _headers(self, authenticated):
        if not authenticated or not self.auth["access_token"]:
            return {}
        return {"Authorization": "{} {}".format(self.auth["token_type"], self.auth["access_token"])}

    @staticmethod
    def _payload(response):
        try:
            # Boosty amounts must never pass through binary floating point.
            # requests.Response.json() does not expose parse_float, therefore
            # parse the original response body explicitly.
            return json.loads(response.text, parse_float=Decimal)
        except ValueError:
            return {"text": response.text[:2000]}

    def refresh(self):
        if not self.auth["refresh_token"]:
            raise BoostyApiError("Boosty refresh token is not configured")
        form = {
            "grant_type": "refresh_token",
            "refresh_token": self.auth["refresh_token"],
        }
        for key in ("client_id", "client_secret", "redirect_uri", "scope"):
            if self.auth[key]:
                form[key] = self.auth[key]
        response = self.session.post(
            self.base_url + "/" + self.refresh_path.lstrip("/"),
            data=form,
            timeout=self.timeout,
        )
        payload = self._payload(response)
        if response.status_code >= 400 or not payload.get("access_token"):
            raise BoostyApiError("Boosty OAuth refresh failed", response.status_code, payload)
        self.auth["access_token"] = str(payload["access_token"])
        self.auth["refresh_token"] = str(payload.get("refresh_token") or self.auth["refresh_token"])
        self.auth["token_type"] = str(payload.get("token_type") or payload.get("tokenType") or "Bearer")
        expires_in = payload.get("expires_in") or payload.get("expiresIn")
        if expires_in:
            self.auth["expires_at"] = int(time.time()) + int(expires_in)
        self._save_auth_state()

    def request(self, method, path, authenticated=True, retry_401=True, **kwargs):
        if authenticated and self.auth["expires_at"] and int(time.time()) + 30 >= int(self.auth["expires_at"]):
            self.refresh()

        last_error = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.request(
                    method,
                    self.base_url + "/" + path.lstrip("/"),
                    headers=self._headers(authenticated),
                    timeout=self.timeout,
                    **kwargs
                )
            except requests.RequestException as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise BoostyApiError("Boosty request failed: {}".format(exc))
                time.sleep(min(self.backoff * (2 ** attempt), self.max_backoff))
                continue

            if response.status_code == 401 and authenticated and retry_401 and self.auth["refresh_token"]:
                self.refresh()
                return self.request(method, path, authenticated=authenticated, retry_401=False, **kwargs)

            if response.status_code == 429 or response.status_code >= 500:
                if attempt < self.retries:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else self.backoff * (2 ** attempt)
                    except (TypeError, ValueError):
                        delay = self.backoff * (2 ** attempt)
                    time.sleep(min(delay, self.max_backoff))
                    continue

            payload = self._payload(response)
            if response.status_code >= 400:
                raise BoostyApiError(
                    "Boosty HTTP {} for {} {}".format(response.status_code, method, path),
                    response.status_code,
                    payload,
                )
            return payload
        raise BoostyApiError("Boosty request failed: {}".format(last_error))

    def donation_sales(self, limit, offset=0):
        payload = self.request(
            "GET",
            "/v1/blog/{}/sales/donation/".format(self.blog),
            params={"limit": int(limit), "offset": int(offset)},
        )
        data = payload.get("data") or {}
        return data.get("donationsSales") or [], payload.get("extra") or {}

    def stat_events(self, timestamp_from, timestamp_to, limit, offset=None):
        params = {
            "from": int(timestamp_from),
            "to": int(timestamp_to),
            "limit": int(limit),
        }
        if offset not in (None, ""):
            params["offset"] = offset
        payload = self.request(
            "GET",
            "/v1/blog/stat/{}/events".format(self.blog),
            params=params,
        )
        return payload.get("data") or [], payload.get("extra") or {}

    def subscribers(self, limit, offset=0):
        payload = self.request(
            "GET",
            "/v1/blog/{}/subscribers".format(self.blog),
            params={"limit": int(limit), "offset": int(offset)},
        )
        return payload.get("data") or [], payload

    def find_dialog_id(self, boosty_user_id, max_pages=20):
        offset = 0
        for _ in range(max_pages):
            payload = self.request("GET", "/v1/dialog/", params={"offset": offset} if offset else None)
            for dialog in payload.get("data") or []:
                chatmate = dialog.get("chatmate") or {}
                if str(chatmate.get("id")) == str(boosty_user_id):
                    return str(dialog.get("id"))
            extra = payload.get("extra") or {}
            if extra.get("isLast") is True:
                break
            next_offset = extra.get("offset")
            if next_offset in (None, offset, str(offset)):
                break
            offset = next_offset
        return None

    def send_dialog_message(self, dialog_id, message):
        editor_payload = json.dumps([
            {
                "type": "text",
                "content": json.dumps([message, "unstyled", []], ensure_ascii=False),
                "modificator": "",
            },
            {"type": "text", "content": "", "modificator": "BLOCK_END"},
        ], ensure_ascii=False)
        return self.request(
            "POST",
            "/v1/dialog/{}/message".format(dialog_id),
            data={"data": editor_payload, "teaser_data": "[]"},
        )
