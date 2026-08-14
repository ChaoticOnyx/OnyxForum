import hashlib
import hmac
import json


def serialize_envelope(event_id, event_name, created_at, data):
    envelope = {
        "eventId": str(event_id),
        "event": event_name,
        "createdAt": created_at.isoformat(),
        "data": data,
    }
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str)


def calculate_signature(secret, timestamp, body):
    signed = "{}.{}".format(timestamp, body).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return "sha256={}".format(digest)
