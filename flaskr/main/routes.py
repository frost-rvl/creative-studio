from flask import current_app, render_template

from flaskr.main import bp


@bp.route("/")
@bp.route("/index")
def index():
    user = {"username": "Miguel"}
    if True:  # Check current_user
        return render_template("landing.html")
    return render_template("index.html", title="Home", user=user)
