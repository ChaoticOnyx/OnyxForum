import datetime
import dateutil.parser
import github.Issue
import traceback
from typing import List

from flask import current_app

from flaskbb.extensions import db_hub

from hub.configs.github_repositories import repositories
from hub.github.issue_queries import QueryGenerator
from hub.github import repository
from hub.models import IssueFull, IssueLabel


def dict_issue_to_db_issue(repository_key: str, dict_issue: dict) -> IssueFull:
    issue = db_hub.session.query(IssueFull).filter(db_hub.and_(IssueFull.number == dict_issue["number"], IssueFull.repository == repository_key)).first()
    if not issue:
        issue = IssueFull()
        issue.repository = repository_key
        issue.number = dict_issue["number"]
        db_hub.session.add(issue)

    issue.title = dict_issue["title"]
    issue.body = dict_issue["body"]
    issue.author = dict_issue["user"]["login"]
    issue.type = 'issue' if "pull_request" not in dict_issue else 'pull_request'
    issue.created_datetime = dateutil.parser.isoparse(dict_issue["created_at"])
    issue.updated_datetime = dateutil.parser.isoparse(dict_issue["updated_at"])
    issue.state = dict_issue["state"]
    
    issue.labels.clear()
    db_hub.session.commit()
    for dict_label in dict_issue["labels"]:
        labels: List = issue.labels
        label = IssueLabel()
        label.repository = issue.repository
        label.issue_number = issue.number
        label.label = dict_label["name"]
        labels.append(label)
    
    db_hub.session.commit()
    return issue


def gh_issue_to_db_issue(repository_key: str, github_issue: github.Issue.Issue) -> IssueFull:
    issue = db_hub.session.query(IssueFull).filter(db_hub.and_(IssueFull.number == github_issue.number, IssueFull.repository == repository_key)).first()
    if not issue:
        issue = IssueFull()
        issue.repository = repository_key
        issue.number = github_issue.number
        db_hub.session.add(issue)

    issue.title = github_issue.title
    issue.body = github_issue.body
    issue.author = github_issue.user.login
    issue.type = 'issue' if github_issue._pull_request.value is None else 'pull_request'
    issue.created_datetime = github_issue.created_at
    issue.updated_datetime = github_issue.updated_at
    issue.state = github_issue.state

    issue.labels.clear()
    for github_label in github_issue.labels:
        labels: List = issue.labels
        label = IssueLabel()
        label.repository = issue.repository
        label.issue_number = issue.number
        label.label = github_label.name
        labels.append(label)
    
    return issue


def actualize_issues_cache(repository_key: str):
    try:
        while True:
            issue: IssueFull = db_hub.session.query(IssueFull).order_by(IssueFull.updated_datetime.desc()).first()

            query_generator = QueryGenerator(repositories[repository_key])
            github_query = query_generator.in_repository() + " " + query_generator.open()
        
            if issue:
                github_query += " updated:>" + issue.updated_datetime.strftime("%Y-%m-%dT%H:%M:%S")

            github_issues = current_app.githubApi.search_issues(github_query, sort="updated", order="asc")

            if not github_issues.totalCount:
                break

            count = 0

            github_issue: github.Issue.Issue
            for github_issue in github_issues:
                issue = gh_issue_to_db_issue(repository_key, github_issue)
                db_hub.session.commit()
                count += 1
                print(f"[actualize_issues_cache] {github_issue.number} actualized ({count}/{github_issues.totalCount})")
    except Exception:
        print("[actualize_issues_cache] exception caught during issues actualization")
        traceback.print_exc()
