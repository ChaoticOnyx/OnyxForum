
from flask import request, current_app, abort
from flaskbb.exceptions import FlaskBBError
from flask_allows import Permission, Requirement
from flaskbb.utils.requirements import Has

from .utils import hub_current_server


class CanAccessServerHub(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            abort(404)

        return bool(Permission(Has(hub_current_server.base_permission), identity=user))


class CanAccessServerHubAdditional(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            raise FlaskBBError("Could not get current server id")

        return bool(Permission(Has(hub_current_server.additional_permission), identity=user))


class CanAccessServerHubManagement(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            raise FlaskBBError("Could not get current server id")

        return bool(Permission(Has(hub_current_server.management_permission), identity=user))


# Template filters

def can_access_hub(user):
    return True
