from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr import db


class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    artworks: so.WriteOnlyMapped["Artwork"] = so.relationship(back_populates="author")

    def __repr__(self) -> str:
        return "<User {}>".format(self.username)


class ArtworkType(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(50), unique=True)
    allowed_extensions: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    max_file_size: so.Mapped[Optional[int]] = so.mapped_column(sa.Integer)
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
    desc: so.Mapped[Optional[str]] = so.mapped_column(sa.String(1024))

    file_path: so.Mapped[str] = so.mapped_column(sa.String(512))
    mime_type: so.Mapped[Optional[str]] = so.mapped_column(sa.String(100))
    file_size: so.Mapped[Optional[str]] = so.mapped_column(sa.Integer)

    def __repr__(self) -> str:
        return "<Art {}>".format(self.title)
