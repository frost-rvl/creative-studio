import os
from flask import (
    abort,
    current_app,
    render_template,
    send_file,
)
from flask_login import current_user, login_required
from flaskr.main import bp

@bp.route("/")
@bp.route("/index")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    
    artworks = current_user.get_followed_artworks()
    return render_template("index.html", title="Home", artworks=artworks)

@bp.route("/uploads/<path:filename>")
@login_required
def serve_uploaded_file(filename):
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, mimetype='image/png')