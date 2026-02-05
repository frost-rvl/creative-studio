import sqlalchemy as sa
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, ValidationError
from wtforms import FileField, StringField, TextAreaField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired, Length

from flaskr import db
from flaskr.models import User


class EditProfileForm(FlaskForm):
    avatar = FileField(
        "Profile picture",
        validators=[FileAllowed(["jpg", "png", "jpeg"])],
        id="avatar-input",
    )
    cover = FileField(
        "Cover photo",
        validators=[FileAllowed(["jpg", "png", "jpeg"])],
        id="cover-input",
    )
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=128)]
    )
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Save changes")

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(
                sa.select(User).where(User.username == username.data)
            )
            if user is not None:
                raise ValidationError("Please use a different username.")
