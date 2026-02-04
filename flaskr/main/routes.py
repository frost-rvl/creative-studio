import os

from flask import abort, current_app, render_template, send_from_directory
from flask_login import current_user

from flaskr.main import bp


@bp.route("/")
@bp.route("/index")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    return render_template("index.html", title="Home")


@bp.route("/uploads/<path:filename>")
def serve_uploaded_file(filename):
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        abort(404)
    direcotry = os.path.dirname(filepath)
    file = os.path.basename(filepath)
    return send_from_directory(direcotry, file)
