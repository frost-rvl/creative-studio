import re

import sqlalchemy as sa
from flask_wtf import FlaskForm
from flask_wtf.recaptcha.validators import ValidationError
from wtforms import BooleanField, PasswordField, StringField
from wtforms.fields import SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from flaskr import db
from flaskr.models import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField(
        "Password", validators=[DataRequired()], id="login-password"
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=128)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8)], id="register-password"
    )
    password2 = PasswordField(
        "Repeat Password",
        validators=[DataRequired(), EqualTo("password")],
        id="repeat-register-password",
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username.")
        if not re.match(r"^[a-zA-Z0-9._-]+$", username.data):
            raise ValidationError(
                "Username can only contain letters, numbers, dots, hyphens, and underscores."
            )

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email.")

    def validate_password(self, password):
        value = password.data
        if not re.search(r"[A-Z]", value):
            raise ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"[a-z]", value):
            raise ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not re.search(r"\d", value):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r"[!@£$%^&*()_+={}?:~\[\]]", value):
            raise ValidationError(
                "Password must contain at least one special character."
            )
