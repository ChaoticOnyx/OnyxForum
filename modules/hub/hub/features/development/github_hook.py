import datetime
import dateutil.parser
from dateutil import tz
import json
import traceback
from typing import List

import github.Repository
from github.Hook import Hook

from flask import Response, request, url_for, current_app
from flask.views import MethodView

from flaskbb.utils.helpers import catch_exceptions

from hub.configs.github_repositories import repositories
from hub.features.development import issues_cache

from hub.features.development.hook_processors.report_priority_increased import *
from hub.features.development.hook_processors.update_issue_cache import *


def process_webhook(content):
    update_issue_cache(content)
    report_priority_increased(content)


class GithubHook(MethodView):
    def post(self):
        content = request.get_json()

        print("[Github Webhooks] Received:")
        print("-- Content:\n" + json.dumps(content, ensure_ascii=False) + "\n----")

        try:
            process_webhook(content)
        except Exception:
            print("Error: Exception is caught during GITHUB hook processing:")
            traceback.print_exc()

        return Response(status=200)


@catch_exceptions
def _register_github_webhooks():
    if not current_app.config["GITHUB_HOOKS"]:
        print("GITHUB Webhooks registration skipped")
        return
    
    for repository_key, repository in repositories.items():
        repo : github.Repository.Repository = current_app.githubApi.get_repo(repository.name)

        url = url_for("development.github_hook", _external=True)

        config = {
            "content_type": "json",
            "url": url,
            "secret": current_app.config["GITHUB_SECRET"],
        }
        events = ["pull_request", "issues", "issue_comment", "label"]

        hooks = repo.get_hooks()
        hook_exists = False
        hook: Hook
        for hook in hooks:
            if hook.url != url:
                continue
            hook_exists = True
            hook.edit("web", config, events, active=True)
            print(f"[Github Webhooks] Webhook for \"{repository.name}\" is updated")

        if not hook_exists:
            repo.create_hook("web", config, events, active=True)
            print(f"[Github Webhooks] Webhook for \"{repository.name}\" is successfuly registered")

        issues_cache.actualize_issues_cache(repository_key)


@catch_exceptions
def _actualize_issues_cache():
    for repository_key, repository in repositories.items():
        issues_cache.actualize_issues_cache(repository_key)


def register_github_webhooks():
    _register_github_webhooks()
    _actualize_issues_cache()
