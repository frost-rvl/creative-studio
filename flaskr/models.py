import os
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from flask_login import UserMixin
from typing_extensions import override
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr import db, login


@login.user_loader
def load_user(id):
    return db.session.get(User, id)


class User(UserMixin, db.Model):
    id: so.Mapped[str] = so.mapped_column(
        sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    artworks: so.WriteOnlyMapped["Artwork"] = so.relationship(back_populates="author")

    about_me: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    avatar_filename: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    cover_filename: so.Mapped[str | None] = so.mapped_column(sa.String(256))

    @override
    def __repr__(self) -> str:
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def avatar(self):
        if self.avatar_filename:
            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                self.username,
                self.avatar_filename,
            )
            if os.path.exists(filepath):
                return url_for(
                    "main.serve_uploaded_file",
                    filename=f"{self.username}/{self.avatar_filename}",
                    _external=True,
                )
        return url_for("static", filename="assets/avatar.jpg", _external=True)

    @property
    def cover(self):
        if self.cover_filename:
            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                self.username,
                self.cover_filename,
            )
            if os.path.exists(filepath):
                return url_for(
                    "main.serve_uploaded_file",
                    filename=f"{self.username}/{self.cover_filename}",
                    _external=True,
                )
        return ""


class ArtworkType(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True)
    allowed_extensions: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    max_file_size: so.Mapped[int | None] = so.mapped_column(sa.Integer)
    artworks: so.WriteOnlyMapped["Artwork"] = so.relationship(
        back_populates="artwork_type"
    )


class Artwork(db.Model):
    id: so.Mapped[str] = so.mapped_column(
        sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: so.Mapped[str] = so.mapped_column(
        sa.String(36), sa.ForeignKey(User.id), index=True
    )
    artwork_type_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(ArtworkType.id), index=True
    )

    author: so.Mapped[User] = so.relationship(back_populates="artworks")
    artwork_type: so.Mapped[ArtworkType] = so.relationship(back_populates="artworks")

    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    title: so.Mapped[str] = so.mapped_column(sa.String(256))
    desc: so.Mapped[str | None] = so.mapped_column(sa.String(1024))

    file_path: so.Mapped[str] = so.mapped_column(sa.String(512))
    mime_type: so.Mapped[str | None] = so.mapped_column(sa.String(100))
    file_size: so.Mapped[str | None] = so.mapped_column(sa.Integer)

    @override
    def __repr__(self) -> str:
        return "<Art {}>".format(self.title)
