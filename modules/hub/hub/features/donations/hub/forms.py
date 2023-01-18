import datetime

from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SubmitField, StringField, SelectField, FloatField, DateTimeField, IntegerField)
from flaskbb.utils.helpers import time_utcnow

from hub.validators import CkeyLinkedToDiscordValidator, IssueIsKnownValidator, DiscordIdValidator
from hub.features.donations import money


class AddDonationForm(FlaskForm):
    datetime = DateTimeField("Datetime", format='%d.%m.%Y %H:%M', default=datetime.datetime.now())
    discord = StringField("Discord ID", validators=[DiscordIdValidator()])
    amount = FloatField("Rubles Donated")
    type = SelectField("Donation Type")
    issue = IntegerField("Issue Number", validators=[IssueIsKnownValidator()], default=0)
    submit = SubmitField("Add Donation")

    def __init__(self):
        super(AddDonationForm, self).__init__()
        self.type.choices = money.get_donation_types()


class AddMoneyTransactionForm(FlaskForm):
    amount = FloatField("Change")
    reason = StringField("Reason")
    submit = SubmitField("Add Transaction")


class AddPointsTransactionForm(FlaskForm):
    discord = StringField("Discord ID", validators=[DiscordIdValidator()])
    amount = FloatField("Change")
    reason = StringField("Reason")
    submit = SubmitField("Add Transaction")
