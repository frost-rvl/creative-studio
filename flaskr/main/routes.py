from flask import render_template
from flask_login import current_user

from flaskr.main import bp


@bp.route("/")
@bp.route("/index")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    return render_template("index.html", title="Home")
