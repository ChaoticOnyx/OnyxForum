import hmac
import logging
from functools import wraps

from flask import current_app, request

logger = logging.getLogger(__name__)

def _compute_github_signature(secret, payload):
    computed = hmac.new(secret.encode("utf-8"), payload, "SHA256")
    return computed.hexdigest()


def _get_github_signature(req):
    gh_signature_header = req.headers.get("X-Hub-Signature-256", "")
    if gh_signature_header and gh_signature_header.startswith("sha256="):
        return gh_signature_header.replace("sha256=", "")
    else:
        return None


def _signatures_are_same(a, b):
    return hmac.compare_digest(a, b)


def verify_github_signature(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "GITHUB_HOOKS" not in current_app.config or not current_app.config["GITHUB_HOOKS"]:
            # Testing hooks
            return f(*args, **kwargs)
        if "GITHUB_SECRET" not in current_app.config:
            msg = "Github Secret isn't configured in app config"
            logger.error(msg)
            return msg, 400
        if request.method != "POST":
            msg = "Signature verification is only supported on POST method!"
            logger.error(msg)
            return msg, 400
        if "X-Hub-Signature-256" not in request.headers:
            msg = "Missing signature header!"
            logger.error(msg)
            return msg, 400
        signature_gh = _get_github_signature(request)
        if signature_gh is not None:
            payload = request.get_data()
            signature = _compute_github_signature(current_app.config["GITHUB_SECRET"], payload)
            if _signatures_are_same(signature, signature_gh):
                return f(*args, **kwargs)
            else:
                msg = f"Signature don't match: {signature} != {signature_gh}"
                logger.error(msg)
                return msg, 400
        else:
            msg = "Signature content isn't valid!"
            logger.error(msg)
            return msg, 400
    
    return decorated_function
