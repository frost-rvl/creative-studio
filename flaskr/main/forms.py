from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length


class EditProfileForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=128)]
    )
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("submit")
