from flask import request, render_template, jsonify, flash, redirect, url_for
from flask_login import current_user, login_required
from flaskr import db
from flaskr.gallery import bp
from flaskr.models import Artwork, ArtworkType
import sqlalchemy as sa
import os

@bp.route("/gallery")
@login_required
def gallery():
    filter_type = request.args.get('type', '')
    artworks = current_user.get_artworks(type_name=filter_type if filter_type else None)
    user_types = current_user.get_artwork_types()
    return render_template(
        "gallery/gallery.html", 
        title="Gallery",
        artworks=artworks,
        user_types=user_types,
        current_filter=filter_type
    )

@bp.route("/artwork/<artwork_id>/toggle-visibility", methods=["POST"])
@login_required
def toggle_visibility(artwork_id):
    artwork = db.session.scalar(
        sa.select(Artwork).where(
            (Artwork.id == artwork_id) & (Artwork.user_id == current_user.id)
        )
    )
    
    if not artwork:
        flash(message="Artwork not found", category="error")
        return redirect(url_for("gallery.gallery"))
    
    artwork.is_public = not artwork.is_public
    db.session.commit()
    
    status = "public" if artwork.is_public else "private"
    flash(message=f"Artwork is now {status}", category="success")
    return redirect(url_for("gallery.gallery"))

@bp.route("/artwork/<artwork_id>/delete", methods=["POST"])
@login_required
def delete_artwork(artwork_id):
    artwork = db.session.scalar(
        sa.select(Artwork).where(
            (Artwork.id == artwork_id) & (Artwork.user_id == current_user.id)
        )
    )
    
    if not artwork:
        flash(message="Artwork not found", category="error")
        return redirect(url_for("gallery.gallery"))
    
    try:
        from flask import current_app
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], artwork.file_path)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        db.session.delete(artwork)
        db.session.commit()
        
        flash(message="Artwork deleted successfully", category="success")
    except Exception as e:
        flash(message=f"Error deleting artwork: {str(e)}", category="error")
    
    return redirect(url_for("gallery.gallery"))