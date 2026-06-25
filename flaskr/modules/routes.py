import uuid
import requests
import sqlalchemy as sa
from flask import render_template, request, url_for, flash, redirect, Response, current_app
from flask_login import login_required, current_user
from flaskr import db
from flaskr.modules import bp
from flaskr.models import Artwork, ArtworkType
from flaskr.utils import save_user_image
from flaskr.modules.forms import ArtworkForm
from werkzeug.datastructures import FileStorage
import base64
import traceback
import os
from io import BytesIO
import re

@bp.route("/modules")
@login_required
def modules_grid():
    return render_template("modules/modules_grid.html", title="Modules")

@bp.route("/modules/<module_name>", methods=["GET", "POST"])
@login_required
def module(module_name):
    form = ArtworkForm()
    
    if form.validate_on_submit():
        image_data_b64 = request.form.get("image_data")
        title = request.form.get("title", "Untitled")
        desc = request.form.get("description", "")
        action = request.form.get("action", "save")
        
        if not image_data_b64:
            flash(message="No image captured", category="error")
            return redirect(url_for("modules.module", module_name=module_name))
        
        try:
            image_bytes = base64.b64decode(image_data_b64)
            file_size = len(image_bytes)

            wrapped_file = FileStorage(
                stream=BytesIO(image_bytes),
                filename="artwork.png",
                content_type="image/png"
            )

            filename = save_user_image(wrapped_file, current_user, kind="artwork")
            
            if filename:
                artwork_type = db.session.scalar(
                    sa.select(ArtworkType).where(ArtworkType.name == module_name)
                )
                
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
                
                flash(message="Artwork saved!", category="success")
                return redirect(url_for('modules.module', module_name=module_name))
        except Exception as e:
            print(f"ERROR: {str(e)}")
            traceback.print_exc()
            flash(message=f"Error saving artwork: {str(e)}", category="error")
    
    module_ports = {
        "zelija": 8000,
        "sablier": 8001,
        "neural_transfer": 8002
    }
    module_port = module_ports.get(module_name)
    module_js = f"{module_name}.js"
    
    return render_template(
        "modules/module.html",
        title="Module",
        module_name=module_name,
        module_port=module_port,
        form=form,
        module_js=module_js
    )

@bp.route('/pygbag/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/pygbag/<path:path>', methods=["GET", "POST"])
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

@bp.route('/sablier/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/sablier/<path:path>', methods=["GET", "POST"])
def proxy_sablier(path):
    url = f'http://localhost:8001/{path}'   # use a new port, e.g., 8003
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

@bp.route('/style-transfer/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/style-transfer/<path:path>', methods=["GET", "POST"])
def proxy_style_transfer(path):
    url = f'http://localhost:8002/{path}'
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
