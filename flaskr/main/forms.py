from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired])
