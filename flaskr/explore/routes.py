from flask import request, render_template
from flask_login import current_user, login_required
from flaskr.explore import bp

@bp.route("/explore")
@login_required
def explore():
    filter_type = request.args.get('type', '')
    artworks = current_user.get_not_followed_artworks(type_name=filter_type if filter_type else None)
    artwork_types = current_user.get_explore_artwork_types()
    
    return render_template(
        "explore/explore.html", 
        title="Explore",
        artworks=artworks,
        artwork_types=artwork_types,
        current_filter=filter_type
    )