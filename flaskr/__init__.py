import logging
import os
from email.utils import formataddr
from logging.handlers import RotatingFileHandler, SMTPHandler

import sqlalchemy as sa
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"  # type: ignore
login.login_message = "Please log in to access this page."
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    from flaskr.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from flaskr.main import bp as main_bp

    app.register_blueprint(main_bp)

    from flaskr.auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    from flaskr.profile import bp as profile_bp

    app.register_blueprint(profile_bp)

    register_db_populate_commands(app)

    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] and app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr=formataddr(
                    ("Creative Studio No-Reply", app.config["MAIL_USERNAME"])
                ),
                toaddrs=app.config["ADMINS"],
                subject="Creative Studio Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists("logs"):
            os.mkdir("logs")
        file_handler = RotatingFileHandler(
            "logs/creative_studio.blog", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.info("Creative Studio Startup")

    return app


def _seed_db_impl() -> None:
    """Implementation of sedd_db command."""
    from flaskr.models import ArtworkType

    art_types = [
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

    for art_type_data in art_types:
        existing = db.session.scalar(
            sa.select(ArtworkType).where(ArtworkType.name == art_type_data["name"])
        )
        if not existing:
            art_type = ArtworkType(**art_type_data)
            db.session.add(art_type)
            print(f"Added artwork type: {art_type_data['name']}")
        else:
            print(f"Artwork type already exists: {art_type_data['name']}")

    db.session.commit()


def register_db_populate_commands(app: Flask) -> None:
    """Register DB population commands for the application."""

    @app.cli.command()
    def seed_db() -> None:
        """Seed the database with inital data."""
        _seed_db_impl()

    @app.cli.command()
    def init_db() -> None:
        """Initialize the database"""
        db.create_all()


from flaskr import models
