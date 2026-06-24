from flask import Blueprint

bp = Blueprint("gallery", __name__)

from flaskr.gallery import routes
