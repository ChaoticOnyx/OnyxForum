import datetime

from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SubmitField, StringField, SelectField, FloatField, DateTimeField)
from wtforms.validators import Optional

from flaskbb.utils.helpers import time_utcnow

from hub.validators import CkeyLinkedToDiscordValidator


class AddDonationForm(FlaskForm):
    datetime = DateTimeField("Datetime", format='%d.%m.%Y %H:%M', default=datetime.datetime.now())
    ckey = StringField("Ckey", validators=[CkeyLinkedToDiscordValidator()])
    amount = FloatField("Rubles Donated")
    type = SelectField("Donation Type", choices=["qiwi", "patreon"])
    submit = SubmitField("Add Donation")


class AddMoneyTransactionForm(FlaskForm):
    amount = FloatField("Change")
    reason = StringField("Reason")
    submit = SubmitField("Add Transaction")


class AddPointsTransactionForm(FlaskForm):
    ckey = StringField("Ckey", validators=[CkeyLinkedToDiscordValidator()])
    amount = FloatField("Change")
    reason = StringField("Reason")
    submit = SubmitField("Add Transaction")
