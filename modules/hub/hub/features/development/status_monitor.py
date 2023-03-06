import discord
import urllib.parse

from flask import current_app
from flaskbb.utils.helpers import discord_task

from hub.github.issue_queries import QueryGenerator
from hub.github.repository import Repository
from hub.configs.github_repositories import repositories

from flaskbb.extensions import scheduler, discordClient

@discord_task
async def send_status(repo: Repository, title: str, description: str, query: str, color: int, channel_key: str):
    issues = current_app.githubApi.search_issues(query)

    if issues.totalCount == 0:
        return

    embed = discord.Embed(title=title)
    embed.color = color
    embed.description = f"**{issues.totalCount}** {description}\n[Список задач](https://github.com/issues?q={urllib.parse.quote(query)})"

    for guild_descriptor in repo.discord_guilds:
        guild: discord.Guild = await discordClient.fetch_guild(guild_descriptor.id)
        channel: discord.TextChannel = await guild.fetch_channel(getattr(guild_descriptor.channels, channel_key))
        await channel.send(embed=embed)


@scheduler.task('cron', id='development_status_monitor', hour=12)
def development_status_monitor():
    with scheduler.app.app_context():
        repo = repositories["onyxbay"]

        send_status(
            repo,
            title="OnyxBay Owners, обратите внимание!",
            description="приоритетных задач ждут вашей реакции",
            query=QueryGenerator(repo).stage_owners(),
            color=0xff4d00,
            channel_key="owners"
        )

        send_status(
            repo,
            title="Issue Watchers, обратите внимание!",
            description="задач ждут проверки",
            query=QueryGenerator(repo).stage_verification(),
            color=0xff4d00,
            channel_key="watchers"
        )

        send_status(
            repo,
            title="Game Designers, обратите внимание!",
            description="приоритетных задач ждут вашей реакции",
            query=QueryGenerator(repo).design_stage(),
            color=0xff4d00,
            channel_key="designers"
        )
