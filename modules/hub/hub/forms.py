from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SubmitField)


class ConfigEditForm(FlaskForm):
    content = TextAreaField()
    submit = SubmitField("Save")
