import json
from decimal import Decimal
from urllib.parse import urlsplit

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, URL, ValidationError

from .settings import endpoint_event_choices, parse_bonus_rules


class BoostySettingsForm(FlaskForm):
    integration_enabled = BooleanField("Integration Enabled")
    polling_interval = IntegerField("Polling Interval (seconds)", validators=[DataRequired(), NumberRange(min=60)])
    automatic_opyx_enabled = BooleanField("Automatic Opyx Processing Enabled")
    opyx_rate = DecimalField("1 RUB = X Opyx", validators=[DataRequired(), NumberRange(min=0)], places=6)
    rounding = SelectField("Rounding", choices=[("floor", "Floor"), ("ceil", "Ceiling"), ("half_up", "Nearest")])
    minimum_donation = DecimalField("Minimum donation amount", validators=[DataRequired(), NumberRange(min=0)], places=2)
    maximum_opyx_enabled = BooleanField("Maximum Opyx per operation enabled")
    maximum_opyx = DecimalField("Maximum Opyx per operation", validators=[Optional(), NumberRange(min=0)], places=2)
    bonus_enabled = BooleanField("Bonus rules enabled")
    bonus_rules = TextAreaField("Bonus rules (JSON)", validators=[Optional()])

    automatic_linking_enabled = BooleanField("Automatic Account Linking Enabled")
    link_token_ttl_minutes = IntegerField("Token TTL (minutes)", validators=[DataRequired(), NumberRange(min=5, max=10080)])

    discord_sync_enabled = BooleanField("Discord Role Synchronization Enabled")
    discord_guild_id = StringField("Discord Guild / Server ID", validators=[Optional(), Length(max=64)])
    donator_role_id = StringField("Donator / Has Opyx Role ID", validators=[Optional(), Length(max=64)])
    donator_role_mode = SelectField("Donator Role Mode", choices=[("Permanent", "Permanent"), ("BalanceBased", "BalanceBased")])

    outgoing_webhooks_enabled = BooleanField("Outgoing Webhooks Enabled")

    message_token = TextAreaField("Message with token", validators=[DataRequired()])
    message_link_success = TextAreaField("Successful link", validators=[DataRequired()])
    message_link_error = TextAreaField("Link error", validators=[DataRequired()])
    message_expired_token = TextAreaField("Expired token", validators=[DataRequired()])
    message_opyx_credited = TextAreaField("Opyx credited", validators=[DataRequired()])
    message_processing_error = TextAreaField("Processing error", validators=[DataRequired()])
    message_link_required = TextAreaField("Account linking required", validators=[DataRequired()])
    submit = SubmitField("Save settings")

    def validate_bonus_rules(self, field):
        try:
            parse_bonus_rules(field.data or "[]")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValidationError("Invalid bonus rules: {}".format(exc))

    def validate_opyx_rate(self, field):
        if field.data is None or field.data <= Decimal("0"):
            raise ValidationError("Opyx rate must be greater than zero")

    def validate_maximum_opyx(self, field):
        if self.maximum_opyx_enabled.data and (field.data is None or field.data <= Decimal("0")):
            raise ValidationError("Maximum Opyx must be greater than zero when the cap is enabled")

    def validate_discord_guild_id(self, field):
        if field.data and not field.data.isdigit():
            raise ValidationError("Discord guild ID must be numeric")

    def validate_donator_role_id(self, field):
        if field.data and not field.data.isdigit():
            raise ValidationError("Discord role ID must be numeric")


class BoostyLinkTokenForm(FlaskForm):
    token = StringField("Boosty one-time token", validators=[DataRequired(), Length(min=20, max=128)])
    submit = SubmitField("Link Boosty account")


class BoostyLinkTokenRequestForm(FlaskForm):
    email = StringField(
        "Email Boosty-аккаунта",
        validators=[DataRequired(), Email(message="Укажите корректный email."), Length(max=255)],
    )
    submit = SubmitField("Запросить новый токен")


class ManualLinkForm(FlaskForm):
    boosty_account_id = IntegerField("Boosty account", validators=[DataRequired()])
    forum_user_id = IntegerField("Forum user ID", validators=[DataRequired()])
    submit = SubmitField("Link account")


class DiscordRoleMappingForm(FlaskForm):
    guild_id = StringField("Guild ID", validators=[DataRequired(), Length(max=64)])
    tier_id = StringField("Boosty tier ID", validators=[DataRequired(), Length(max=64)])
    tier_name = StringField("Boosty tier name", validators=[Optional(), Length(max=255)])
    role_id = StringField("Discord role ID", validators=[DataRequired(), Length(max=64)])
    enabled = BooleanField("Enabled", default=True)
    submit = SubmitField("Save mapping")

    def validate_guild_id(self, field):
        if not field.data.isdigit():
            raise ValidationError("Discord guild ID must be numeric")

    def validate_role_id(self, field):
        if not field.data.isdigit():
            raise ValidationError("Discord role ID must be numeric")


class WebhookEndpointForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=255)])
    url = StringField("URL", validators=[DataRequired(), URL(), Length(max=2048)])
    enabled = BooleanField("Enabled", default=True)
    secret = PasswordField("Secret", validators=[Optional(), Length(min=16, max=512)])
    events = SelectMultipleField("Events", choices=endpoint_event_choices(), validators=[DataRequired()])
    timeout_seconds = IntegerField("Timeout (seconds)", validators=[DataRequired(), NumberRange(min=1, max=120)])
    retry_count = IntegerField("Retry count", validators=[DataRequired(), NumberRange(min=0, max=20)])
    submit = SubmitField("Save endpoint")

    def validate_url(self, field):
        if urlsplit(field.data).scheme.lower() not in ("http", "https"):
            raise ValidationError("Webhook URL must use HTTP or HTTPS")


class IgnoreOperationForm(FlaskForm):
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=3, max=2000)])
    submit = SubmitField("Mark as ignored")


class CorrectionForm(FlaskForm):
    amount = DecimalField("Opyx amount", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(min=3, max=2000)])
    submit = SubmitField("Create correction")
