import discord
from flask import current_app
from flaskbb.extensions import db
from datetime import datetime
from sqlalchemy import exists

from flaskbb.extensions import discord, discordClient
from flaskbb.utils.helpers import discord_task
from hub.servers_config import ServerDescriptor

class WhitelistApplication(db.Model):
    __tablename__ = "whitelist_applications"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(length=255), nullable=False)
    ckey = db.Column(db.String(length=255), nullable=False)
    source_type = db.Column(db.Enum('forum', 'channel', name='source_type'), nullable=False)
    source_id = db.Column(db.String(length=255), nullable=False)  # канал или тред
    message_id = db.Column(db.String(length=255), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    comments = db.Column(db.JSON, nullable=True)  # список словарей: [{author, content}]
    status = db.Column(
        db.Enum('pending', 'accepted', 'rejected', name='whitelist_status'),
        default='pending'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@discord_task
async def fetch_whitelist_applications(server_descriptor, guild_id):
    channel_id = int(server_descriptor.whitelist_channel)

    guild = await discordClient.fetch_guild(guild_id)
    channel = await discordClient.fetch_channel(channel_id)

    applications = []

    if isinstance(channel, discord.ForumChannel):
        threads = channel.threads
        for thread in threads:
            messages = [msg async for msg in thread.history(limit=10)]
            if not messages:
                continue

            first_message = messages[-1]
            ckey = thread.name.strip().lower()

            already_exists = db.session.query(
                exists().where(WhitelistApplication.message_id == first_message.id)
            ).scalar()

            if not already_exists:
                app = WhitelistApplication(
                    server_id=server_descriptor.id,
                    ckey=ckey,
                    source_type='forum',
                    source_id=str(thread.id),
                    message_id=str(first_message.id),
                    message_text=first_message.content,
                    comments=[
                        {"author": m.author.name, "content": m.content}
                        for m in reversed(messages[:-1])
                    ],
                    created_at=first_message.created_at
                )
                db.session.add(app)
                applications.append(app)

    elif isinstance(channel, discord.TextChannel):
        async for message in channel.history(limit=100):
            if message.author.bot:
                continue

            if " " not in message.content and "\n" not in message.content:
                continue  # явно не заявка

            ckey = message.content.split()[0].lower()
            text = message.content[len(ckey):].strip()

            already_exists = db.session.query(
                exists().where(WhitelistApplication.message_id == message.id)
            ).scalar()

            if not already_exists:
                app = WhitelistApplication(
                    server_id=server_descriptor.id,
                    ckey=ckey,
                    source_type='channel',
                    source_id=str(channel.id),
                    message_id=str(message.id),
                    message_text=text,
                    comments=None,
                    created_at=message.created_at
                )
                db.session.add(app)
                applications.append(app)

    if applications:
        db.session.commit()

    return applications

@discord_task
async def respond_to_application(app, action, guild_id):
    with current_app.app_context():
        import discord
        client = discordClient
        guild = await discordClient.fetch_guild(guild_id)
        # Перезагружаем объект приложения, чтобы он был связан с текущей сессией
        app = db.session.merge(app)  # Заново связываем сессией
        server = ServerDescriptor.query.get(app.server_id)
        server = db.session.merge(server)  # Заново связываем сессией

        if app.source_type == "forum":
            thread = await discordClient.fetch_channel(int(app.source_id))
            await thread.send(
                f"Заявка от `{app.ckey}` на сервер `{server.name}` была {'принята ✅' if action == 'accept' else 'отклонена ❌'}."
            )
            message = await thread.fetch_message(int(app.message_id))
            emoji = "✅" if action == "accept" else "❌"
            await message.add_reaction(emoji)
            await thread.edit(locked=True, archived=True)
            try:
                member = await guild.fetch_member(message.author.id)
                if action == "accept":
                    await member.add_roles(guild.get_role(int(server.whitelist_role)))
                dm = await member.create_dm()
                await dm.send(
                    f"Ваша заявка на сервер `{server.name}` была {'принята ✅' if action == 'accept' else 'отклонена ❌'}."
                )
            except Exception:
                pass  # на случай если ЛС отключены

        elif app.source_type == "channel":
            channel = await discordClient.fetch_channel(int(app.source_id))
            message = await channel.fetch_message(int(app.message_id))
            emoji = "✅" if action == "accept" else "❌"
            await message.add_reaction(emoji)
            try:
                member = await guild.fetch_member(message.author.id)
                if action == "accept":
                    await member.add_roles(guild.get_role(int(server.whitelist_role)))
                dm = await member.create_dm()
                await dm.send(
                    f"Ваша заявка на сервер `{server.name}` была {'принята ✅' if action == 'accept' else 'отклонена ❌'}."
                )
            except Exception:
                pass  # на случай если ЛС отключены

@discord_task
async def remove_whitelist_emoji(app, guild_id):
    with current_app.app_context():
        # Перезагружаем объект приложения, чтобы он был связан с текущей сессией
        app = db.session.merge(app)  # Заново связываем сессией
        server = ServerDescriptor.query.get(app.server_id)
        server = db.session.merge(server)  # Заново связываем сессией

        client = discordClient
        guild = await discordClient.fetch_guild(guild_id)
        channel = await discordClient.fetch_channel(int(app.source_id))
        message = await channel.fetch_message(int(app.message_id))
        member = await guild.fetch_member(message.author.id)
        await member.remove_roles(guild.get_role(int(server.whitelist_role)))
        await message.clear_reaction("✅")  # если понадобится
