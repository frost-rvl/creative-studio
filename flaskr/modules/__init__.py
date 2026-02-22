from flask import Blueprint

bp = Blueprint("modules", __name__)

from flaskr.modules import routes
