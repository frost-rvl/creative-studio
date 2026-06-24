import os
import uuid
from datetime import datetime, timezone
from time import time

import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from flask_login import UserMixin
from typing_extensions import override
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr import db, login

followers = sa.Table(
    "followers",
    db.metadata,
    sa.Column("follower_id", sa.String(36), sa.ForeignKey("user.id"), primary_key=True),
    sa.Column("followed_id", sa.String(36), sa.ForeignKey("user.id"), primary_key=True),
)


@login.user_loader
def load_user(id):
    return db.session.get(User, id)


class User(UserMixin, db.Model):
    id: so.Mapped[str] = so.mapped_column(
        sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    is_verified: so.Mapped[sa.Boolean] = so.mapped_column(sa.Boolean(), default=False)

    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256))
    artworks: so.WriteOnlyMapped["Artwork"] = so.relationship(back_populates="author")

    about_me: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    avatar_filename: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    cover_filename: so.Mapped[str | None] = so.mapped_column(sa.String(256))

    following: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates="followers",
    )

    followers: so.WriteOnlyMapped["User"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates="following",
    )

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

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery()
        )
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery()
        )
        return db.session.scalar(query)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except Exception:
            return
        return db.session.get(User, id)

    def get_email_verification_token(self, expires_in=600):
        return jwt.encode(
            {"verify_email": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    def set_email_verified(self):
        self.is_verified = True  # type: ignore

    @staticmethod
    def verify_email_verification_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["verify_email"]
        except Exception:
            return
        return db.session.get(User, id)

    def get_artworks(self, type_name=None):
        query = sa.select(Artwork).where(Artwork.user_id == self.id)
        if type_name:
            query = query.join(ArtworkType).where(ArtworkType.name == type_name)
        query = query.order_by(Artwork.timestamp.desc())
        return db.session.scalars(query).all()
    
    def get_artwork_types(self):
        query = sa.select(ArtworkType).join(Artwork).where(Artwork.user_id == self.id).distinct()
        return db.session.scalars(query).all()

    def get_followed_artworks(self):
        query = sa.select(Artwork).where(
            (Artwork.user_id.in_(
                self.following.select().with_only_columns(User.id)
            )) & 
            (Artwork.is_public == True)
        ).order_by(Artwork.timestamp.desc())
        return db.session.scalars(query).all()

    def get_not_followed_artworks(self, type_name=None):
        query = sa.select(Artwork).where(
            (Artwork.user_id.notin_(
                self.following.select().with_only_columns(User.id)
            )) & 
            (Artwork.user_id != self.id) &
            (Artwork.is_public == True)
        )
        
        if type_name:
            query = query.join(ArtworkType).where(ArtworkType.name == type_name)
        
        query = query.order_by(Artwork.timestamp.desc())
        return db.session.scalars(query).all()

    def get_explore_artwork_types(self):
        query = sa.select(ArtworkType).join(Artwork).where(
            (Artwork.user_id.notin_(
                self.following.select().with_only_columns(User.id)
            )) & 
            (Artwork.user_id != self.id) &
            (Artwork.is_public == True)
        ).distinct()
        return db.session.scalars(query).all()


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
    
    is_public: so.Mapped[bool] = so.mapped_column(sa.Boolean(), default=False)
    file_path: so.Mapped[str] = so.mapped_column(sa.String(512))
    mime_type: so.Mapped[str | None] = so.mapped_column(sa.String(100))
    file_size: so.Mapped[int | None] = so.mapped_column(sa.Integer)

    @override
    def __repr__(self) -> str:
        return "<Art {}>".format(self.title)
