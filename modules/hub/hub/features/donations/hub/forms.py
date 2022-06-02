import datetime

from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SubmitField, StringField, SelectField, FloatField, DateTimeField, IntegerField)
from wtforms.validators import Optional

from flaskbb.utils.helpers import time_utcnow

from hub.validators import CkeyLinkedToDiscordValidator, IssueIsKnownValidator
from hub.features.donations import money


class AddDonationForm(FlaskForm):
    datetime = DateTimeField("Datetime", format='%d.%m.%Y %H:%M', default=datetime.datetime.now())
    ckey = StringField("Ckey", validators=[CkeyLinkedToDiscordValidator()])
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
    ckey = StringField("Ckey", validators=[CkeyLinkedToDiscordValidator()])
    amount = FloatField("Change")
    reason = StringField("Reason")
    submit = SubmitField("Add Transaction")
