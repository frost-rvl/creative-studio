import sqlalchemy as sa
from flask import render_template
from flask_login import current_user, login_required

from flaskr import db
from flaskr.main import bp
from flaskr.models import User


@bp.route("/")
@bp.route("/index")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    return render_template("index.html", title="Home")


@bp.route("/user/<username>")
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    return render_template("user.html", user=user)
