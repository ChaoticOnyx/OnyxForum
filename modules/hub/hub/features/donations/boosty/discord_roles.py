import logging

from flask import current_app
from sqlalchemy import func

from flaskbb.extensions import db_hub, discordClient
from flaskbb.utils.helpers import discord_task, time_utcnow

from hub.models import PointsTransaction

from .constants import DISCORD_FAILED, DISCORD_PENDING, DISCORD_PROCESSED, OPERATION_PROCESSED
from .models import (
    BoostyAccount,
    BoostyDiscordAction,
    BoostyDiscordRoleMapping,
    BoostyOperation,
    BoostyProcessingEvent,
)
from .settings import get_settings
from .webhooks import queue_event


logger = logging.getLogger("donations.boosty.discord")


def queue_account_role_sync(account_id, operation_id=None, include_donator=False):
    settings = get_settings()
    if not settings.get("boosty_discord_sync_enabled"):
        return None
    guild_id = str(settings.get("boosty_discord_guild_id") or "")
    if not guild_id:
        return None
    action = BoostyDiscordAction(
        operation_id=operation_id,
        account_id=account_id,
        guild_id=guild_id,
        action="Sync",
        status=DISCORD_PENDING,
    )
    db_hub.session.add(action)
    db_hub.session.commit()
    _synchronize_roles(action.id, include_donator)
    return action


def queue_role_removal(account_id, guild_id, role_id, discord_user_id=None):
    """Remove a role that is ceasing to be managed by a deleted mapping."""
    action = BoostyDiscordAction(
        account_id=account_id,
        guild_id=str(guild_id),
        discord_user_id=str(discord_user_id) if discord_user_id else None,
        role_id=str(role_id),
        action="RemoveRole",
        status=DISCORD_PENDING,
    )
    db_hub.session.add(action)
    db_hub.session.commit()
    _synchronize_roles(action.id)
    return action


def process_pending_role_actions(limit=50):
    settings = get_settings()
    if not settings.get("boosty_discord_sync_enabled"):
        return 0
    action_ids = [
        item[0] for item in
        BoostyDiscordAction.query.with_entities(BoostyDiscordAction.id)
        .filter_by(status=DISCORD_PENDING, attempts=0)
        .order_by(BoostyDiscordAction.created_at.asc())
        .limit(limit)
        .all()
    ]
    for action_id in action_ids:
        _synchronize_roles(action_id, True)
    return len(action_ids)


def _record_role_action(action, role_id, action_name):
    item = BoostyDiscordAction(
        operation_id=action.operation_id,
        account_id=action.account_id,
        guild_id=action.guild_id,
        discord_user_id=action.discord_user_id,
        role_id=str(role_id),
        action=action_name,
        status=DISCORD_PROCESSED,
        attempts=1,
        processed_at=time_utcnow(),
    )
    db_hub.session.add(item)
    if action.operation_id:
        db_hub.session.add(BoostyProcessingEvent(
            operation_id=action.operation_id,
            event="DiscordRoleAssigned" if action_name == "Assign" else "DiscordRoleRemoved",
            details={"roleId": str(role_id), "guildId": action.guild_id},
        ))
    event_name = "boosty.discord.role.assigned" if action_name == "Assign" else "boosty.discord.role.removed"
    queue_event(event_name, {
        "accountId": action.account_id,
        "discordUserId": action.discord_user_id,
        "guildId": action.guild_id,
        "roleId": str(role_id),
    }, action.operation_id)


@discord_task
async def _synchronize_roles(action_id, include_donator=False):
    action = BoostyDiscordAction.query.get(action_id)
    if action is None:
        return
    action.attempts += 1
    try:
        settings = get_settings()
        if not settings.get("boosty_discord_sync_enabled"):
            db_hub.session.rollback()
            return
        account = BoostyAccount.query.get(action.account_id)
        if account is None:
            raise RuntimeError("Boosty account does not exist")
        if not action.discord_user_id:
            if account.link is None or not account.link.player.discord_user_id:
                raise RuntimeError("Boosty account is not linked to a Discord player")
            action.discord_user_id = str(account.link.player.discord_user_id)
        guild = await discordClient.fetch_guild(int(action.guild_id))
        member = await guild.fetch_member(int(action.discord_user_id))
        roles = await guild.fetch_roles()
        roles_by_id = {str(role.id): role for role in roles}
        current_role_ids = {str(role.id) for role in member.roles}

        if action.action == "RemoveRole":
            role = roles_by_id.get(str(action.role_id))
            if role and str(action.role_id) in current_role_ids:
                await member.remove_roles(role)
                queue_event("boosty.discord.role.removed", {
                    "accountId": action.account_id,
                    "discordUserId": action.discord_user_id,
                    "guildId": action.guild_id,
                    "roleId": str(action.role_id),
                })
            action.status = DISCORD_PROCESSED
            action.processed_at = time_utcnow()
            action.last_error = None
            db_hub.session.commit()
            return

        mappings = BoostyDiscordRoleMapping.query.filter_by(guild_id=action.guild_id).all()
        managed_tier_role_ids = {str(mapping.role_id) for mapping in mappings}
        desired_tier_role_ids = set()
        if account.is_paid_subscriber and account.tier_id:
            desired_tier_role_ids = {
                str(mapping.role_id) for mapping in mappings
                if mapping.enabled and str(mapping.tier_id) == str(account.tier_id)
            }

        remove_ids = (current_role_ids & managed_tier_role_ids) - desired_tier_role_ids
        add_ids = desired_tier_role_ids - current_role_ids
        for role_id in remove_ids:
            role = roles_by_id.get(role_id)
            if role:
                await member.remove_roles(role)
                _record_role_action(action, role_id, "Remove")
        for role_id in add_ids:
            role = roles_by_id.get(role_id)
            if role is None:
                raise RuntimeError("Configured Discord role {} was not found".format(role_id))
            await member.add_roles(role)
            _record_role_action(action, role_id, "Assign")

        donator_role_id = str(settings.get("boosty_donator_role_id") or "")
        if include_donator and donator_role_id:
            role = roles_by_id.get(donator_role_id)
            if role is None:
                raise RuntimeError("Configured Donator role {} was not found".format(donator_role_id))
            should_have = (
                BoostyOperation.query
                .filter_by(account_id=account.id, status=OPERATION_PROCESSED)
                .filter(BoostyOperation.points_transaction_id.isnot(None))
                .count() > 0
            )
            if settings.get("boosty_donator_role_mode") == "BalanceBased":
                balance = (
                    db_hub.session.query(func.sum(PointsTransaction.change))
                    .filter(PointsTransaction.player_id == account.link.player_id)
                    .scalar() or 0
                )
                should_have = balance > 0
            has_role = donator_role_id in current_role_ids
            if should_have and not has_role:
                await member.add_roles(role)
                _record_role_action(action, donator_role_id, "Assign")
            elif not should_have and has_role and settings.get("boosty_donator_role_mode") == "BalanceBased":
                await member.remove_roles(role)
                _record_role_action(action, donator_role_id, "Remove")

        action.status = DISCORD_PROCESSED
        action.processed_at = time_utcnow()
        action.last_error = None
        db_hub.session.commit()
    except Exception as exc:
        db_hub.session.rollback()
        action = BoostyDiscordAction.query.get(action_id)
        if action is None:
            logger.exception("Boosty Discord action %s disappeared during synchronization", action_id)
            return
        action.attempts += 1
        action.status = DISCORD_FAILED
        action.last_error = str(exc)
        if action.operation_id:
            db_hub.session.add(BoostyProcessingEvent(
                operation_id=action.operation_id,
                event="DiscordRoleError",
                message=str(exc),
                details={"actionId": action.id, "guildId": action.guild_id},
            ))
        try:
            queue_event("boosty.discord.role.error", {
                "actionId": action.id,
                "accountId": action.account_id,
                "guildId": action.guild_id,
                "error": str(exc),
            }, action.operation_id)
        except Exception:
            logger.exception("Failed to queue Discord error webhook for action %s", action_id)
        db_hub.session.commit()
        logger.exception("Boosty Discord synchronization failed for action %s", action_id)


def retry_discord_action(action):
    action.status = DISCORD_PENDING
    action.last_error = None
    db_hub.session.commit()
    _synchronize_roles(action.id, True)
