from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, StringField, TextAreaField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length


class EditProfileForm(FlaskForm):
    avatar = FileField(
        "Profile picture",
        validators=[FileAllowed(["jpg", "png", "jpeg"])],
    )
    cover = FileField(
        "Cover photo",
        validators=[FileAllowed(["jpg", "png", "jpeg"])],
    )
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=128)]
    )
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Save changes")
