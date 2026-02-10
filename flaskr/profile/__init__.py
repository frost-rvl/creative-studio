from flask import Blueprint

bp = Blueprint("profile", __name__)

from flaskr.profile import routes
