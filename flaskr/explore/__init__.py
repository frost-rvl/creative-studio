from flask import Blueprint

bp = Blueprint("explore", __name__)

from flaskr.explore import routes
