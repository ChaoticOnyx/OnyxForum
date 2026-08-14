import json
from urllib.parse import urlparse


def is_discord_webhook_url(url):
    """Return true only for Discord's webhook URL shape."""
    try:
        parsed = urlparse(str(url or ""))
    except ValueError:
        return False
    hostname = (parsed.hostname or "").lower()
    is_discord_host = hostname in ("discord.com", "discordapp.com") or hostname.endswith(".discord.com")
    return parsed.scheme == "https" and is_discord_host and parsed.path.startswith("/api/webhooks/")


def serialize_delivery_payload(envelope, endpoint_url):
    """Serialize a canonical envelope or its Discord presentation adapter."""
    if not is_discord_webhook_url(endpoint_url):
        return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)

    event_name = str(envelope.get("event") or "boosty.event")
    event_id = str(envelope.get("eventId") or "")
    description = json.dumps(
        envelope.get("data") or {},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
    if len(description) > 4000:
        description = description[:3997] + "..."
    payload = {
        "content": "Boosty event: `{}`".format(event_name)[:2000],
        "embeds": [{
            "title": event_name[:256],
            "description": description,
            "timestamp": envelope.get("createdAt"),
            "footer": {"text": "Event ID: {}".format(event_id)[:2048]},
        }],
        "allowed_mentions": {"parse": []},
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)
