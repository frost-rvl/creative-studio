import sqlalchemy as sa
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from flaskr import db
from flaskr.main.forms import EmptyForm
from flaskr.models import User
from flaskr.profile import bp
from flaskr.profile.forms import EditProfileForm
from flaskr.utils import rename_user_folder, save_user_image


@bp.route("/user/<username>")
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    return render_template("profile/user.html", title="Profile", user=user, form=form)


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    old_username = current_user.username
    if form.validate_on_submit():
        if form.username.data != old_username:
            rename_user_folder(old_username, form.username.data)  # type: ignore
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        avatar = form.avatar.data
        cover = form.cover.data

        if avatar and avatar.filename:
            try:
                filename = save_user_image(avatar, current_user, kind="avatar")
                if filename:
                    current_user.avatar_filename = filename
            except Exception as e:
                flash(message=f"Error uploading avatar: {str(e)}", category="error")

        if cover and cover.filename:
            try:
                filename = save_user_image(cover, current_user, kind="cover")
                if filename:
                    current_user.cover_filename = filename
            except Exception as e:
                flash(message=f"Error uploading cover: {str(e)}", category="error")

        db.session.commit()
        flash(message="Your changes have been saved.", category="success")
        return redirect(url_for("profile.user", username=current_user.username))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("profile/edit_profile.html", title="Edit Profile", form=form)


@bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(message=f"User {username} not found.", category="info")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(message="You cannont follow yourself", category="warning")
            return redirect(url_for("profile.user", username=username))
        current_user.follow(user)
        db.session.commit()
        flash(message=f"You are following {username}!", category="success")
        return redirect(url_for("profile.user", username=username))
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == username))
        if user is None:
            flash(message=f"User {username} not found.", category="info")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash(message="You cannot unfollow yourself!", category="warning")
            return redirect(url_for("profile.user", username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(message=f"You are not following {username}!", category="info")
        return redirect(url_for("profile.user", username=username))
    else:
        return redirect(url_for("main.index"))
