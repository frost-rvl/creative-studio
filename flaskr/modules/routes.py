import uuid
import requests
import sqlalchemy as sa
from flask import render_template, request, url_for, flash, redirect, Response
from flask_login import login_required, current_user
from flaskr import db
from flaskr.modules import bp
from flaskr.models import Artwork, ArtworkType
from flaskr.utils import save_user_image
from flaskr.modules.forms import ArtworkForm

@bp.route("/modules")
@login_required
def modules_grid():
    return render_template("modules/modules_grid.html", title="Modules")

@bp.route("/modules/<module_name>", methods=["GET", "POST"])
@login_required
def module(module_name):
    form = ArtworkForm()
    
    if request.method == "POST":
        print("=== POST RECEIVED ===")
        print(f"Module: {module_name}")
        print(f"Files: {request.files.keys()}")
        print(f"Form data: {request.form.keys()}")
        
        file = request.files.get("artwork_image")
        title = request.form.get("title", "Untitled")
        desc = request.form.get("description", "")
        action = request.form.get("action", "save")
        
        print(f"File: {file.filename if file else 'None'}")
        print(f"Title: {title}")
        print(f"Action: {action}")
        
        if not file or file.filename == "":
            flash(message="No image captured", category="error")
            return redirect(url_for("modules.module", module_name=module_name))
        
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            print(f"Saving file... size: {file_size}")
            filename = save_user_image(file, current_user, kind=f"artwork_{uuid.uuid4().hex}")
            
            if filename:
                print(f"File saved: {filename}")
                
                artwork_type = db.session.scalar(
                    sa.select(ArtworkType).where(ArtworkType.name == module_name)
                )
                print(f"ArtworkType: {artwork_type}")
                
                artwork = Artwork(
                    user_id=current_user.id,
                    artwork_type_id=artwork_type.id if artwork_type else None,
                    title=title,
                    desc=desc,
                    file_path=f"{current_user.username}/{filename}",
                    mime_type="image/png",
                    file_size=file_size,
                    is_public=(action == "share")
                )
                db.session.add(artwork)
                db.session.commit()
                
                print("Artwork saved to DB!")
                flash(message="Artwork saved!", category="success")
                return redirect(url_for("main.index"))
        except Exception as e:
            print(f"ERROR: {str(e)}")
            flash(message=f"Error saving artwork: {str(e)}", category="error")
    
    module_ports = {"zelija": 8000}
    module_port = module_ports.get(module_name)
    
    return render_template(
        "modules/module.html",
        title="Module",
        module_name=module_name,
        module_port=module_port,
        form=form
    )

@bp.route('/pygbag/', defaults={'path': ''})
@bp.route('/pygbag/<path:path>')
def proxy_pygbag(path):
    url = f'http://localhost:8000/{path}'
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}
    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        stream=True,
        allow_redirects=False
    )
    return Response(
        resp.iter_content(chunk_size=1024),
        status=resp.status_code,
        headers=dict(resp.headers)
    )
