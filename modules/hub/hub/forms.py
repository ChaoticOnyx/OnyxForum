from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SubmitField, StringField, SelectField)


class ConfigEditForm(FlaskForm):
    content = TextAreaField()
    submit = SubmitField("Save")


class BanSearchForm(FlaskForm):
    searchText = StringField("Search Text")
    searchType = SelectField("Search Field", choices=["Ckey", "Admin", "Reason"])
    searchButton = SubmitField("Search")


class ConnectionSearchForm(FlaskForm):
    searchText = StringField("Search Text")
    searchType = SelectField("Search Field", choices=["Ckey", "Computer ID", "IP"])
    searchButton = SubmitField("Search")
