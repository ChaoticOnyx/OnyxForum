import discord
from datetime import datetime
from dateutil import tz
from typing import Optional, List

from flask import current_app
from flaskbb.user.models import User
from flaskbb.utils.helpers import discord_task
from flaskbb.extensions import discordClient, db_hub
from flaskbb.utils.settings import flaskbb_config

from hub.features.donations.utils import get_donations_host_user, get_player_points_sum
from hub.models import PatronType, PointsTransaction, MoneyTransaction, PatronSubscription


async def __get_discord_role(role_id: str) -> Optional[discord.Role]:
    if not role_id:
        return None
    guild: discord.Guild = await discordClient.fetch_guild(current_app.config["COMMUNITY_GUILD_ID"])
    return guild.get_role(int(role_id))


async def __try_send_to_user_and_host(user: discord.User, ckey, host, embed, host_title, user_title):
    assert user
    assert embed
    assert host
    assert host_title
    assert user_title

    embed.title = host_title
    if host:
        await host.send(embed=embed)

    if not user:
        return

    embed.title = user_title
    try:
        await user.send(embed=embed)
    except discord.errors.Forbidden:
        await host.send("**Ошибка:** Discord запретил отправку сообщения {ckey} ({discord} - {discord_id})"
            .format(ckey=ckey, discord="{}#{}".format(user.name, user.discriminator), discord_id=user.id))
        raise
    except Exception:
        await host.send("**Ошибка:** Произошла неизвестная ошибка при отправке сообщения {ckey} ({discord} - {discord_id})"
            .format(ckey=ckey, discord="{}#{}".format(user.name, user.discriminator), discord_id=user.id))
        raise


@discord_task
async def notify_user_donation_registration_error(dt: datetime, amount, comment: str):
    host = await get_donations_host_user()

    if not comment:
        comment = "<Отсутствует>"

    color = 0xff0000
    embed = discord.Embed(color=color)
    embed.title = "Неполучилось автоматически обработать донат!"
    embed.add_field(name="Время", value=dt.strftime("%d.%m.%y %H:%M"), inline=False)
    embed.add_field(name="Рублей задоначено", value=amount, inline=False)
    embed.add_field(name="Комментарий", value=comment, inline=False)

    if host:
        await host.send(embed=embed)


@discord_task
async def notify_user_about_points_transaction(initiator: User, transaction: PointsTransaction):
    if initiator:
        initiator: discord.User = await discordClient.fetch_user(int(initiator.discord))
    else:
        initiator = await get_donations_host_user()

    color = 0xff0000 if transaction.change < 0 else 0xffd000
    embed = discord.Embed(color=color)

    embed.add_field(name="Аккаунт BYOND", value=transaction.player.ckey, inline=False)
    embed.add_field(
        name="Потрачено опиксов" if transaction.change < 0 else "Добавлено опиксов",
        value="{:+.0f}".format(transaction.change),
        inline=False)
    embed.add_field(name="Комментарий", value=transaction.comment, inline=False)
    embed.add_field(name="Время транзакции", value=transaction.datetime.astimezone(tz.tzlocal()).strftime("%d.%m.%y %H:%M"), inline=False)

    user: discord.User = None
    if transaction.player.discord_user_id:
        user = await discordClient.fetch_user(int(transaction.player.discord_user_id))

    await __try_send_to_user_and_host(
        user=user,
        ckey=transaction.player.ckey,
        host=initiator,
        embed=embed,
        host_title="{}#{}".format(user.name, user.discriminator) if user else "Неизвестный пользователь" + \
                  (" потратил опиксы." if transaction.change < 0 else " получил опиксы."),
        user_title="Вы потратили опиксы!" if transaction.change < 0 else "Вы получили опиксы!")


@discord_task
async def notify_user_about_subscription_update(subscriptions: List[PatronSubscription]):
    assert subscriptions
    assert len(subscriptions)

    host = await get_donations_host_user()
    embed = discord.Embed()
    max_patron_type: PatronType = None
    for subscription in subscriptions:
        if not max_patron_type or max_patron_type.cost_dollars < subscription.patron_type.cost_dollars:
            max_patron_type = subscription.patron_type
        patron_role = await __get_discord_role(subscription.patron_type.discord_role)
        embed.add_field(
            name=patron_role.name,
            value="С {} по {}".format(
                subscription.start_date.strftime("%d.%m.%y"),
                subscription.end_date.strftime("%d.%m.%y"),
                inline=False))

    max_patron_role = await __get_discord_role(max_patron_type.discord_role)
    embed.color=max_patron_role.color

    user: discord.User = None
    if subscriptions[0].player.discord_user_id:
        user = await discordClient.fetch_user(int(subscriptions[0].player.discord_user_id))

    await __try_send_to_user_and_host(
        user=user,
        ckey=subscriptions[0].player.ckey,
        host=host,
        embed=embed,
        host_title= "Подписка "
                    "{}#{}".format(user.name, user.discriminator) if user else "неизвестного пользователя обновлена",
        user_title= "Ваша подписка Onyx обновлена")


@discord_task
async def report_money_transaction(balance, transaction: MoneyTransaction):
    reports_channel = discordClient.get_channel(current_app.config["DONATIONS_REPORT_CHANNEL_ID"])
    timestr = transaction.datetime.astimezone(tz.tzlocal()).strftime("%d.%m.%Y %H:%M")

    if transaction.change > 0:
        await reports_channel.send(
            "__{}__ _получили **{:+.0f} ₽**. Сумма: {:.0f} ₽._".format(timestr, transaction.change, balance))
    else:
        await reports_channel.send(
            "__{}__ _{}: **{:+.0f} ₽**. Сумма: {:.0f} ₽._".format(timestr, transaction.reason, transaction.change, balance))


@discord_task
async def report_points_transaction(transaction: PointsTransaction):
    reports_channel = discordClient.get_channel(current_app.config["DONATIONS_POINTS_REPORT_CHANNEL_ID"])

    player_str = ""
    if transaction.player:
        player_str = transaction.player.ckey or f"{transaction.player.discord_user.nickname} ({transaction.player.discord_user_id})"

    message = None
    if transaction.change > 0:
        message = "\n_**{}** добавили **{:+.0f}** опиксов: \"{}\"_".format(
                player_str,
                transaction.change,
                transaction.comment)
    else:
        message = "\n_**{}** сняли **{:+.0f}** опиксов: \"{}\"_".format(
                player_str,
                transaction.change,
                transaction.comment)

    summary = get_player_points_sum(transaction.player)
    message += "\n_Текущий баланс: {:.0f} опиксов._".format(summary)
    await reports_channel.send(message)


@discord_task
async def report_subscription_update(subscriptions: List[PatronSubscription]):
    assert subscriptions
    assert len(subscriptions)

    player_str = ""
    if subscriptions[0].player:
        player_str = subscriptions[0].player.ckey or f"{subscriptions[0].player.discord_user.nickname} ({subscriptions[0].player.discord_user_id})"

    reports_channel = discordClient.get_channel(current_app.config["DONATIONS_POINTS_REPORT_CHANNEL_ID"])

    message = ""
    for subscription in subscriptions:
        patron_role = await __get_discord_role(subscription.patron_type.discord_role)
        message += "\n**{role}:** {start} -> {end}".format(
            role=patron_role.name,
            start=subscription.start_date.strftime("%d.%m.%y"),
            end=subscription.end_date.strftime("%d.%m.%y"))

    message = f"Подписка **{player_str}** обновлена:" + message
    message = "_" + message + "_"
    await reports_channel.send(message)
