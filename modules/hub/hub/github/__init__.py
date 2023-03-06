import github
from flask import current_app

from hub.configs.github_repositories import repositories

def create_github_api() -> github.Github:
    githubApi = github.Github(current_app.config["GITHUB_TOKEN"])
    for repository in repositories.values():
        repository.init(githubApi)
    return githubApi
