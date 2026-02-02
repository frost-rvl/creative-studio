from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.fields import SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField(
        "Password", validators=[DataRequired()], id="login-password"
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")
