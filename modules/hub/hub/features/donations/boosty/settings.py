from copy import deepcopy

from flask import current_app

from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.forms import SettingValueType

from .constants import LEGACY_MESSAGE_DEFAULTS, MESSAGE_DEFAULTS, WEBHOOK_EVENTS
from .opyx import parse_bonus_rules


DEFAULT_SETTINGS = {
    "boosty_integration_enabled": False,
    "boosty_polling_interval": 60,
    "boosty_automatic_opyx_enabled": True,
    "boosty_opyx_rate": "2",
    "boosty_rounding": "floor",
    "boosty_minimum_donation": "0",
    "boosty_maximum_opyx_enabled": False,
    "boosty_maximum_opyx": "0",
    "boosty_bonus_enabled": False,
    "boosty_bonus_rules": "[]",
    "boosty_automatic_linking_enabled": True,
    "boosty_link_token_ttl_minutes": 60,
    "boosty_discord_sync_enabled": False,
    "boosty_discord_guild_id": "",
    "boosty_donator_role_id": "",
    "boosty_donator_role_mode": "Permanent",
    "boosty_outgoing_webhooks_enabled": False,
}
DEFAULT_SETTINGS.update(MESSAGE_DEFAULTS)


def _setting(value, value_type, name, description, extra=None):
    return {
        "value": value,
        "value_type": value_type,
        "name": name,
        "description": description,
        "extra": extra or {},
    }


def _rounding_choices():
    return [("floor", "Floor"), ("ceil", "Ceiling"), ("half_up", "Nearest")]


def _donator_mode_choices():
    return [("Permanent", "Permanent"), ("BalanceBased", "Balance based")]


PLUGIN_SETTINGS = {
    "boosty_integration_enabled": _setting(False, SettingValueType.boolean, "Boosty integration enabled", "Global Boosty polling switch."),
    "boosty_polling_interval": _setting(60, SettingValueType.integer, "Boosty polling interval", "Polling interval in seconds; the cfg value is used as the installation default.", {"min": 60}),
    "boosty_automatic_opyx_enabled": _setting(True, SettingValueType.boolean, "Automatic Opyx processing", "Automatically credit linked donations."),
    "boosty_opyx_rate": _setting("2", SettingValueType.string, "RUB to Opyx rate", "How many Opyx are credited per RUB."),
    "boosty_rounding": _setting("floor", SettingValueType.select, "Opyx rounding", "Rounding applied after rate and bonus.", {"choices": _rounding_choices}),
    "boosty_minimum_donation": _setting("0", SettingValueType.string, "Minimum donation", "Donations below this RUB value are ignored."),
    "boosty_maximum_opyx_enabled": _setting(False, SettingValueType.boolean, "Maximum Opyx enabled", "Cap Opyx credited by one operation."),
    "boosty_maximum_opyx": _setting("0", SettingValueType.string, "Maximum Opyx", "Maximum Opyx per operation when enabled."),
    "boosty_bonus_enabled": _setting(False, SettingValueType.boolean, "Bonus rules enabled", "Apply threshold bonus rules."),
    "boosty_bonus_rules": _setting("[]", SettingValueType.string, "Bonus rules", 'JSON list, for example [{"minimum":"1000","percent":"5"}].'),
    "boosty_automatic_linking_enabled": _setting(True, SettingValueType.boolean, "Automatic account linking", "Generate and send one-time link tokens."),
    "boosty_link_token_ttl_minutes": _setting(60, SettingValueType.integer, "Link token TTL", "One-time token lifetime in minutes.", {"min": 5}),
    "boosty_discord_sync_enabled": _setting(False, SettingValueType.boolean, "Discord role synchronization", "Synchronize only roles managed by Boosty mappings."),
    "boosty_discord_guild_id": _setting("", SettingValueType.string, "Discord guild", "Guild/server ID used by the Boosty integration."),
    "boosty_donator_role_id": _setting("", SettingValueType.string, "Donator / Has Opyx role", "Independent role assigned after a processed donation."),
    "boosty_donator_role_mode": _setting("Permanent", SettingValueType.select, "Donator role mode", "Permanent keeps the role after the first credit.", {"choices": _donator_mode_choices}),
    "boosty_outgoing_webhooks_enabled": _setting(False, SettingValueType.boolean, "Outgoing webhooks", "Queue configured webhook deliveries."),
}

for key, value in MESSAGE_DEFAULTS.items():
    PLUGIN_SETTINGS[key] = _setting(
        value,
        SettingValueType.string,
        key.replace("boosty_message_", "").replace("_", " ").title(),
        "Editable Boosty message template.",
    )


def get_settings():
    result = deepcopy(DEFAULT_SETTINGS)
    configured_default = current_app.config.get("BOOSTY_POLLING_INTERVAL_SECONDS")
    if configured_default:
        result["boosty_polling_interval"] = int(configured_default)

    plugin = PluginRegistry.query.filter_by(name="hub").first()
    if plugin:
        result.update(plugin.settings)
        # Adopt improved defaults on existing installations without replacing
        # message templates that an administrator has actually customized.
        for key, legacy_value in LEGACY_MESSAGE_DEFAULTS.items():
            if result.get(key) == legacy_value:
                result[key] = MESSAGE_DEFAULTS[key]
    return result


def endpoint_event_choices():
    return [(event, event) for event in WEBHOOK_EVENTS]
