from flask import Blueprint

bp = Blueprint("errors", __name__)

from flaskr.errors import handlers
