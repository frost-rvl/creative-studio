import sqlalchemy as sa
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from flaskr import db
from flaskr.main import bp
from flaskr.main.forms import EditProfileForm
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


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.", "info")
        return redirect(url_for("main.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)
