from datetime import datetime, timezone
from hashlib import md5
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from typing_extensions import override
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr import db, login


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    artworks: so.WriteOnlyMapped["Artwork"] = so.relationship(back_populates="author")

    about_me: so.Mapped[str | None] = so.mapped_column(sa.String(140))

    @override
    def __repr__(self) -> str:
        return "<User {}>".format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
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
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
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
