from flaskbb.utils.helpers import catch_exceptions

from hub.configs.github_repositories import repositories, get_repository
from hub.features.development import issues_cache

@catch_exceptions
def update_issue_cache(content):
    if "issue" in content:
        issue = content["issue"]
    elif "pull_request" in content:
        issue = content["pull_request"]
    else:
        return 

    repository_key, _ = get_repository(repositories, content["repository"]["full_name"])
    db_issue = issues_cache.dict_issue_to_db_issue(repository_key, issue)
    print(f"[update_issue_cache] {db_issue.number} updated")
