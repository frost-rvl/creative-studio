import os

import click
import sqlalchemy as sa
from flask import Blueprint

bp = Blueprint("cli", __name__, cli_group=None)


@bp.cli.command("seed-db")
def seed_db():
    """Seed the database with initial data."""
    from flaskr import db
    from flaskr.models import ArtworkType

    artwork_types = [
        {
            "name": "generative_art",
            "allowed_extensions": "jpg,jpeg,png,gif,webp,mp4,webm",
            "max_file_size": 20 * 1024 * 1024,  # 20MB
        },
        {
            "name": "data_visualization",
            "allowed_extensions": "jpg,jpeg,png,svg,pdf,html",
            "max_file_size": 10 * 1024 * 1024,  # 10MB
        },
        {
            "name": "audio_manipulation",
            "allowed_extensions": "mp3,wav,ogg,m4a,flac",
            "max_file_size": 25 * 1024 * 1024,  # 25MB
        },
        {
            "name": "image_manipulation",
            "allowed_extensions": "jpg,jpeg,png,gif,webp,bmp",
            "max_file_size": 15 * 1024 * 1024,  # 15MB
        },
        {
            "name": "ai_project",
            "allowed_extensions": "zip,tar,gz,pdf,mp4,jpg,png",
            "max_file_size": 50 * 1024 * 1024,  # 50MB
        },
    ]
    for artwork_type_data in artwork_types:
        existing = db.session.scalar(
            sa.select(ArtworkType).where(ArtworkType.name == artwork_type_data["name"])
        )
        if not existing:
            artwork_type = ArtworkType(**artwork_type_data)
            db.session.add(artwork_type)
            print(f"Added artwork type: {artwork_type_data['name']}")
        else:
            print(f"Artwork type already exists: {artwork_type_data['name']}")
    db.session.commit()
