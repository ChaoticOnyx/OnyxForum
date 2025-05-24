
from flask import request, current_app, abort
from flaskbb.exceptions import FlaskBBError
from flask_allows import Permission, Requirement
from flaskbb.utils.requirements import Has

from .utils import hub_current_server


def aggregate_hub_permissions(user) -> dict:
    result = {}

    if not getattr(user, "is_authenticated", False):
        return {}
        
    if user.primary_group and user.primary_group.hub_permissions:
        result.update(user.primary_group.hub_permissions)

    for group in user.secondary_groups:
        if group.hub_permissions:
            result.update(group.hub_permissions)

    return result

class CanAccessServerHub(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            abort(404)

        permissions = aggregate_hub_permissions(user)
        key = f"{hub_current_server.id}_base"
        return permissions.get(key, False)


class CanAccessServerHubAdditional(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            raise FlaskBBError("Could not get current server id")

        permissions = aggregate_hub_permissions(user)
        key = f"{hub_current_server.id}_additional"
        return permissions.get(key, False)


class CanAccessServerHubManagement(Requirement):
    def fulfill(self, user):
        if not hub_current_server:
            raise FlaskBBError("Could not get current server id")

        permissions = aggregate_hub_permissions(user)
        key = f"{hub_current_server.id}_management"
        return permissions.get(key, False)


# Template filters

def can_access_hub(user):
    return True
