from flaskbb.utils.helpers import catch_exceptions

from hub.configs.github_repositories import repositories, get_repository
from hub.features.development import issues_cache

@catch_exceptions
def update_issue_cache(content):
    if not "issue" in content:
        return
    repository_key, _ = get_repository(repositories, content["repository"]["full_name"])
    issue = content["issue"]
    db_issue = issues_cache.dict_issue_to_db_issue(repository_key, issue)
    print(f"[update_issue_cache] {db_issue.number} updated")
