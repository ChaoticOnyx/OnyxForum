import discord
from discord import app_commands

from flask import current_app

from flaskbb.extensions import discordCommandsTree
from flaskbb.utils.helpers import discord_task

from hub.configs.github_repositories import repositories

from .status_monitor import *


@discord_task
async def register_commands():
    guild_ids = [discord_guild.id for repo in repositories for discord_guild in repositories[repo].discord_guilds]
    guilds = [discord.Object(id=id) for id in guild_ids]

    group = app_commands.Group(name="devstatus", description="Development Status Commands", guild_ids=guild_ids)

    group.add_command(
        app_commands.Command(
            name = "design",
            description = "Design Stage Issues Status",
            callback=current_app.add_discord_callback(status_designers)))
    
    group.add_command(
        app_commands.Command(
            name = "owners",
            description = "Owners Stage Issues Status",
            callback=current_app.add_discord_callback(status_owners)))
    
    group.add_command(
        app_commands.Command(
            name = "watchers",
            description = "Watchers Stage Issues Status",
            callback=current_app.add_discord_callback(status_watchers)))
    
    group.add_command(
        app_commands.Command(
            name = "developers",
            description = "Development Stage Items Status",
            callback=current_app.add_discord_callback(status_developers)))
    
    group.add_command(
        app_commands.Command(
            name = "bounties",
            description = "Issues with Bounty",
            callback=current_app.add_discord_callback(status_bounties)))
    
    group.add_command(
        app_commands.Command(
            name = "spriters",
            description = "Sprite Issues",
            callback=current_app.add_discord_callback(status_spriters)))
    
    group.add_command(
        app_commands.Command(
            name = "beginners",
            description = "Beginner Issues",
            callback=current_app.add_discord_callback(status_beginners)))
    
    discordCommandsTree.add_command(group)
    
    for guild in guilds:
        await discordCommandsTree.sync(guild=guild)
