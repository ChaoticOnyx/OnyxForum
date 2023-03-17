import asyncio
import discord
import urllib.parse

from flask import current_app
from flaskbb.utils.helpers import discord_task

from hub.github.issue_queries import QueryGenerator
from hub.github.repository import Repository
from hub.configs.github_repositories import repositories

from flaskbb.extensions import scheduler, discordClient

from .discord_utils import send_embed

def create_owners_status_embed():
    repo = repositories["onyxbay"]

    query_max_priority = QueryGenerator(repo).stage_owners_max_priority()
    max_priority_issues = current_app.githubApi.search_issues(query_max_priority)

    query_high_priority = QueryGenerator(repo).stage_owners_high_priority()
    high_priority_issues = current_app.githubApi.search_issues(query_high_priority)

    embed = discord.Embed(title="СТАТУС: OnyxBay Owners")
    embed.color = 0x069c0d
    embed.description = \
        "**Ожидают апрува:**\n" \
        f"**{max_priority_issues.totalCount}** [критических задач](https://github.com/issues?q={urllib.parse.quote(query_max_priority)}) ожидают апрува\n" \
        f"**{high_priority_issues.totalCount}** [задач повышенного приоритета](https://github.com/issues?q={urllib.parse.quote(query_high_priority)}) ожидают апрува"
    
    return embed

def create_developers_status_embed():
    repo = repositories["onyxbay"]

    query_max_priority = QueryGenerator(repo).stage_development_bugs_max_priority()
    max_priority_issues = current_app.githubApi.search_issues(query_max_priority)

    query_high_priority = QueryGenerator(repo).stage_development_bugs_high_priority()
    high_priority_issues = current_app.githubApi.search_issues(query_high_priority)

    query_review_required_prs_priority = QueryGenerator(repo).pr_review_required(priority=True)
    review_required_prs_priority = current_app.githubApi.search_issues(query_review_required_prs_priority)

    query_review_required_prs = QueryGenerator(repo).pr_review_required(priority=False)
    review_required_prs = current_app.githubApi.search_issues(query_review_required_prs)

    embed = discord.Embed(title="СТАТУС: Разработка")
    embed.color = 0xff8b00
    embed.description = \
        "**Количество багов:**\n" \
        f"**{max_priority_issues.totalCount}** [критических багов](https://github.com/issues?q={urllib.parse.quote(query_max_priority)})\n" \
        f"**{high_priority_issues.totalCount}** [багов повышенного приоритета](https://github.com/issues?q={urllib.parse.quote(query_high_priority)})\n" \
        "\n" \
        "**ПРов ожидает ревью:**\n" \
        f"**{review_required_prs_priority.totalCount}** [приоритетных ПРов](https://github.com/issues?q={urllib.parse.quote(query_review_required_prs_priority)})\n" \
        f"**{review_required_prs.totalCount}** [обычных ПРов](https://github.com/issues?q={urllib.parse.quote(query_review_required_prs)})\n" \
    
    return embed

def create_bounty_embed():
    repo = repositories["onyxbay"]

    query_bounties = QueryGenerator(repo).bounty()
    bounty_issues = current_app.githubApi.search_issues(query_bounties)

    embed = discord.Embed(title="СТАТУС: Денежные награды")
    embed.color = 0xffc900
    embed.description = \
        "**Задачи с денежной наградой:**\n" \
        f"**{bounty_issues.totalCount}** [задач с выставленными наградами](https://github.com/issues?q={urllib.parse.quote(query_bounties)})"
    
    return embed

def create_spriters_status_embed():
    repo = repositories["onyxbay"]

    query_max_priority = QueryGenerator(repo).sprites_max_priority()
    max_priority_issues = current_app.githubApi.search_issues(query_max_priority)

    query_high_priority = QueryGenerator(repo).sprites_high_priority()
    high_priority_issues = current_app.githubApi.search_issues(query_high_priority)

    embed = discord.Embed(title="СТАТУС: спрайты")
    embed.color = 0x7eb871
    embed.description = "**Ожидаются спрайты:**\n" \
        f"**{max_priority_issues.totalCount}** [спрайтов нужны с максимальным приоритетом](https://github.com/issues?q={urllib.parse.quote(query_max_priority)})\n" \
        f"**{high_priority_issues.totalCount}** [спрайтов нужны с повышенным приоритетом](https://github.com/issues?q={urllib.parse.quote(query_high_priority)})"
    
    return embed

def create_beginners_status_embed():
    repo = repositories["onyxbay"]

    query_beginners = QueryGenerator(repo).beginners()
    beginners_issues = current_app.githubApi.search_issues(query_beginners)

    embed = discord.Embed(title="СТАТУС: простые задачи")
    embed.color = 0xff8b00
    embed.description = "**Простые задачи:**\n" \
        f"**{beginners_issues.totalCount}** [простых задач доступно](https://github.com/issues?q={urllib.parse.quote(query_beginners)})"
    
    return embed


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
        
        send_embed(
            repo,
            create_owners_status_embed(),
            channel_keys=["owners"])
        
        send_embed(
            repo,
            create_developers_status_embed(),
            channel_keys=["developers"])

        send_embed(
            repo,
            create_spriters_status_embed(),
            channel_keys=["spriters"]
        )

        send_embed(
            repo,
            create_beginners_status_embed(),
            channel_keys=["beginners"]
        )

        send_embed(
            repo,
            create_bounty_embed(),
            channel_keys=["developers"]
        )

        send_status(
            repo,
            title="Issue Watchers, обратите внимание!",
            description="задач ждут проверки",
            query=QueryGenerator(repo).stage_verification(),
            color=0xff8b00,
            channel_key="watchers"
        )

        send_status(
            repo,
            title="Game Designers, обратите внимание!",
            description="приоритетных задач ждут вашей реакции",
            query=QueryGenerator(repo).stage_design(),
            color=0xff4d00,
            channel_key="designers"
        )


async def status_owners(interaction: discord.Interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    embed = create_owners_status_embed()

    await interaction.edit_original_response(embed=embed)

async def status_developers(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    embed = create_developers_status_embed()

    await interaction.edit_original_response(embed=embed)

async def status_bounties(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    embed = create_bounty_embed()

    await interaction.edit_original_response(embed=embed)

async def status_spriters(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    embed = create_spriters_status_embed()

    await interaction.edit_original_response(embed=embed)

async def status_beginners(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    embed = create_beginners_status_embed()

    await interaction.edit_original_response(embed=embed)

async def status_watchers(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    repo = repositories["onyxbay"]
    query = QueryGenerator(repo).stage_verification()
    api = current_app.githubApi
    issues = api.search_issues(query)

    embed = discord.Embed(title="СТАТУС: Watchers")
    embed.color = 0xff8b00
    embed.description = f"**{issues.totalCount}** задач ожидают проверки\n[Список задач](https://github.com/issues?q={urllib.parse.quote(query)})"

    await interaction.edit_original_response(embed=embed)

async def status_designers(interaction):
    response = interaction.response
    asyncio.create_task(response.defer())

    repo = repositories["onyxbay"]
    query = QueryGenerator(repo).stage_design()
    api = current_app.githubApi
    issues = api.search_issues(query)

    embed = discord.Embed(title="СТАТУС: Design")
    embed.color = 0x175f29
    embed.description = f"**{issues.totalCount}** критических задачи ожидают проработки\n[Список задач](https://github.com/issues?q={urllib.parse.quote(query)})"

    await interaction.edit_original_response(embed=embed)
