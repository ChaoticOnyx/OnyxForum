import discord
from typing import List

from flaskbb.extensions import discordClient
from flaskbb.utils.helpers import discord_task

from hub.github import repository

@discord_task
async def send_embed(repo: repository.Repository, embed, channel_keys: List[str]):
    for guild_descriptor in repo.discord_guilds:
        guild: discord.Guild = await discordClient.fetch_guild(guild_descriptor.id)
        for channel_key in channel_keys:
            channel: discord.TextChannel = await guild.fetch_channel(getattr(guild_descriptor.channels, channel_key))
        await channel.send(embed=embed)
