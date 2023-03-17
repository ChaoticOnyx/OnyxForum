import discord

from flaskbb.utils.helpers import catch_exceptions

from hub.configs.github_repositories import repositories, get_repository
from hub.features.development.discord_utils import send_embed
from hub.github import repository


def create_priority_increased_embed(dict_issue, dict_sender, repository: repository.Repository, is_pr):
    embed = discord.Embed(title=f"Повышен приоритет")
    embed.color = 0xebd534
    type = "Задача" if not is_pr else "ПР"
    embed.description = f"[{type} #{dict_issue['number']}: {dict_issue['title']}]({dict_issue['html_url']})"

    labels = "\n".join([label["name"] for label in dict_issue["labels"]])
    embed.add_field(name="Лейблы:", value=labels)

    for dict_label in dict_issue["labels"]:
        if dict_label["name"] == repository.labels.priority_max.name:
            embed.title = "Максимальный приоритет!"
            embed.color = 0xeb3434

    embed.add_field(name="Изменил:", value=dict_sender["login"])
    
    return embed


@catch_exceptions
def report_priority_increased(content):
    if not "action" in content or content["action"] != "labeled":
        return
    
    is_pr = False
    if "issue" in content:
        issue = content["issue"]
    elif "pull_request" in content:
        issue = content["pull_request"]
        is_pr = True
    else:
        return 

    if issue["state"] != "open":
        return
    
    _, repository = get_repository(repositories, content["repository"]["full_name"])

    new_label = content["label"]
    if new_label["name"] != repository.labels.priority_high.name and \
       new_label["name"] != repository.labels.priority_max.name:
        return
    
    embed = create_priority_increased_embed(issue, content["sender"], repository, is_pr)
    send_embed(repository, embed, ["webhook"])
