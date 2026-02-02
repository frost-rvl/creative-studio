import sqlalchemy as sa
import sqlalchemy.orm as so

from flaskr import create_app, db
from flaskr.models import Artwork, ArtworkType, User

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "sa": sa,
        "so": so,
        "db": db,
        "User": User,
        "Artwork": Artwork,
        "ArtworkType": ArtworkType,
    }
