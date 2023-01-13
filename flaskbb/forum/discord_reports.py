from pluggy import HookimplMarker

from flask import current_app, url_for
from flaskbb.extensions import discord, discordClient
from flaskbb.utils.helpers import discord_task

from .models import Topic, Post

@discord_task
async def report_new_topic(channel, topic_id, title, content, author, url):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    channel: discord.TextChannel = await guild.fetch_channel(channel)

    desc = content
    desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc
    embed = discord.Embed(title=title, description=desc, url=url, color=0x8fb57d)
    embed.add_field(name="Author:", value=author)

    message: discord.Message = await channel.send(embed=embed)
    topic: Topic = Topic.query.filter_by(id=topic_id).first()
    if topic:
        topic.first_post.discord_message_id = message.id
        topic.save()


@discord_task
async def report_new_post(channel, post_id, topic_title, content, author, url):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    channel: discord.TextChannel = await guild.fetch_channel(channel)

    desc = content
    desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc
    title = author + " answered to \"" + topic_title + "\""
    embed = discord.Embed(title=title, description=desc, url=url)

    message: discord.Message = await channel.send(embed=embed)
    post: Post = Post.query.filter_by(id=post_id).first()
    if post:
        post.discord_message_id = message.id
        post.save()


@discord_task
async def update_topic_report(channel, message_id, title, content, author, url):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    channel: discord.TextChannel = await guild.fetch_channel(channel)
    message: discord.Message = await channel.fetch_message(message_id)

    desc = content
    desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc
    embed = discord.Embed(title=title, description=desc, url=url, color=0x8fb57d)
    embed.add_field(name="Author:", value=author)

    await message.edit(embed=embed)

@discord_task
async def update_post_report(channel, message_id, topic_title, content, author, url):
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    channel: discord.TextChannel = await guild.fetch_channel(channel)
    message: discord.Message = await channel.fetch_message(message_id)

    desc = content
    desc = (desc[:2000] + "\n...") if len(desc) > 2000 else desc
    title = author + " answered to \"" + topic_title + "\""
    embed = discord.Embed(title=title, description=desc, url=url)

    await message.edit(embed=embed)


hookimpl = HookimplMarker("flaskbb")


@hookimpl
def flaskbb_event_topic_save_after(topic: Topic, is_new: bool):
    if not topic.forum.discord_report_channel:
        return
    if not is_new:
        if topic.first_post.discord_message_id:
            update_topic_report(
                channel=topic.forum.discord_report_channel,
                message_id=topic.first_post.discord_message_id,
                title=topic.title,
                content=topic.first_post.content,
                author=topic.user.display_name,
                url=url_for("forum.view_topic", topic_id=topic.id, slug=topic.slug, _external=True)
            )
        return
    report_new_topic(
        channel=topic.forum.discord_report_channel,
        topic_id=topic.id,
        title=topic.title,
        content=topic.first_post.content,
        author=topic.user.display_name,
        url=url_for("forum.view_topic", topic_id=topic.id, slug=topic.slug, _external=True))


@hookimpl
def flaskbb_event_post_save_after(post: Post, is_new: bool):
    if not post.topic.forum.discord_report_channel:
        return
    if not is_new:
        if not post.discord_message_id:
            return
        update_post_report(
            channel=post.topic.forum.discord_report_channel,
            message_id=post.discord_message_id,
            topic_title=post.topic.title,
            content=post.content,
            author=post.user.display_name,
            url=url_for("forum.view_post", post_id=post.id,  _external=True)
        )
        return
    if not post.topic.forum.discord_report_posts or not post.topic.first_post_id:
        return
    report_new_post(
        channel=post.topic.forum.discord_report_channel,
        post_id=post.id,
        topic_title=post.topic.title,
        content=post.content,
        author=post.user.display_name,
        url=url_for("forum.view_post", post_id=post.id,  _external=True)
    )
