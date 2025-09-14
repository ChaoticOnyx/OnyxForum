import discord as dpy 
from flask import current_app
from flaskbb.extensions import db
from datetime import datetime
from sqlalchemy import exists

from flaskbb.extensions import discord, discordClient, scheduler
from flaskbb.utils.helpers import discord_task
from hub.servers_config import ServerDescriptor
from .jobs import normalize_jobs_from_text

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
    jobs = db.Column(db.JSON, nullable=True)                 # список канонических job
    jobs_unknown = db.Column(db.JSON, nullable=True)         # список нераспознанных токенов
    jobs_valid = db.Column(db.Boolean, default=None)         # True/False/None
    jobs_valid_reason = db.Column(db.Text, nullable=True)    # почему невалидно (если False)

@scheduler.task(
    'interval',
    id='schedule_task_fetch_whitelist_applications',
    hours=2,
    coalesce=True,
    max_instances=1,
    misfire_grace_time=300
)
def schedule_task_fetch_whitelist_applications():
    with scheduler.app.app_context():
        servers = (ServerDescriptor.query
                   .filter(ServerDescriptor.whitelist_channel != "" or ServerDescriptor.job_whitelist_channel != "")
                   .all())

        guild_id = int(current_app.config["COMMUNITY_GUILD_ID"])

        for server in servers:
            try:
                whitelist_channel = server.whitelist_channel.strip()
                if whitelist_channel.isdigit():
                    if(server.whitelist_channel != ""):
                        fetch_whitelist_applications(server, guild_id, int(server.whitelist_channel))

                job_whitelist_channel = server.job_whitelist_channel.strip()
                if job_whitelist_channel.isdigit():
                    if(server.job_whitelist_channel != ""):
                        fetch_whitelist_applications(server, guild_id, int(server.job_whitelist_channel))
            except Exception as e:
                current_app.logger.warning(
                    f"[Job] Failed to enqueue fetch_whitelist_applications for server_id={getattr(server, 'id', '?')}: {e}"
                )

@discord_task
async def fetch_whitelist_applications(server_descriptor, guild_id, channel_id):

    guild = await discordClient.fetch_guild(guild_id)
    channel = await discordClient.fetch_channel(channel_id)

    applications = []
    created = 0
    updated = 0

    def compute_job_fields(text: str):
        valid_jobs, unknown_jobs = normalize_jobs_from_text(text)
        jobs_valid = bool(valid_jobs) and not unknown_jobs
        reason = None
        if not jobs_valid:
            if not valid_jobs and not unknown_jobs:
                reason = "No jobs detected in application text."
            elif unknown_jobs:
                reason = "Unknown job tokens: " + ", ".join(unknown_jobs)
        return valid_jobs or None, unknown_jobs or None, jobs_valid, reason

    if isinstance(channel, dpy.ForumChannel):
        threads = channel.threads
        for thread in threads:
            if getattr(thread, "locked", False) or getattr(thread, "archived", False):
                continue

            messages = [msg async for msg in thread.history(limit=10)]
            if not messages:
                continue

            first_message = messages[-1]
            ckey = thread.name.strip().lower()

            jobs, jobs_unknown, jobs_valid, jobs_reason = compute_job_fields(first_message.content)
            app = (WhitelistApplication.query
                   .filter_by(message_id=str(first_message.id))
                   .one_or_none())

            if app is None:
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
                    created_at=first_message.created_at,
                    jobs=jobs,
                    jobs_unknown=jobs_unknown,
                    jobs_valid=jobs_valid,
                    jobs_valid_reason=jobs_reason,
                )
                db.session.add(app)
                applications.append(app)
                created += 1
            else:
                if app.status == 'pending':
                    changed = False

                    new_comments = [
                        {"author": m.author.name, "content": m.content}
                        for m in reversed(messages[:-1])
                    ]

                    if app.ckey != ckey:
                        app.ckey = ckey; changed = True
                    if app.message_text != first_message.content:
                        app.message_text = first_message.content; changed = True
                    if (app.comments or []) != new_comments:
                        app.comments = new_comments; changed = True
                    if (app.jobs or []) != (jobs or []):
                        app.jobs = jobs; changed = True
                    if (app.jobs_unknown or []) != (jobs_unknown or []):
                        app.jobs_unknown = jobs_unknown; changed = True
                    if app.jobs_valid != jobs_valid:
                        app.jobs_valid = jobs_valid; changed = True
                    if app.jobs_valid_reason != jobs_reason:
                        app.jobs_valid_reason = jobs_reason; changed = True

                    if changed:
                        updated += 1

    elif isinstance(channel, dpy.TextChannel):
        async for message in channel.history(limit=100):
            if message.author.bot:
                continue

            if " " not in message.content and "\n" not in message.content:
                continue  # явно не заявка

            ckey = message.content.split()[0].lower()
            text = message.content[len(ckey):].strip()

            jobs, jobs_unknown, jobs_valid, jobs_reason = compute_job_fields(text)

            app = (WhitelistApplication.query
                   .filter_by(message_id=str(message.id))
                   .one_or_none())

            if app is None:
                app = WhitelistApplication(
                    server_id=server_descriptor.id,
                    ckey=ckey,
                    source_type='channel',
                    source_id=str(channel.id),
                    message_id=str(message.id),
                    message_text=text,
                    comments=None,
                    created_at=message.created_at,
                    jobs=jobs,
                    jobs_unknown=jobs_unknown,
                    jobs_valid=jobs_valid,
                    jobs_valid_reason=jobs_reason,
                )
                db.session.add(app)
                applications.append(app)
                created += 1
            else:
                if app.status == 'pending':
                    changed = False

                    if app.ckey != ckey:
                        app.ckey = ckey; changed = True
                    if app.message_text != text:
                        app.message_text = text; changed = True
                    if (app.jobs or []) != (jobs or []):
                        app.jobs = jobs; changed = True
                    if (app.jobs_unknown or []) != (jobs_unknown or []):
                        app.jobs_unknown = jobs_unknown; changed = True
                    if app.jobs_valid != jobs_valid:
                        app.jobs_valid = jobs_valid; changed = True
                    if app.jobs_valid_reason != jobs_reason:
                        app.jobs_valid_reason = jobs_reason; changed = True

                    if changed:
                        updated += 1

    if created or updated:
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
