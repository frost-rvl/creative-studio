from flask import Flask

from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from flaskr.main import bp as main_bp

    app.register_blueprint(main_bp)

    from flaskr.auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    return app
