import uuid
import requests
import sqlalchemy as sa
import re
import base64
import traceback
import os
from io import BytesIO
from flask import render_template, request, url_for, flash, redirect, Response, current_app
from flask_login import login_required, current_user
from werkzeug.datastructures import FileStorage

from flaskr import db
from flaskr.modules import bp
from flaskr.models import Artwork, ArtworkType
from flaskr.utils import save_user_image
from flaskr.modules.forms import ArtworkForm


# ─── HELPERS ────────────────────────────────────────────────────────────────────

COOP_COEP = {
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Embedder-Policy': 'credentialless',
    'Cross-Origin-Resource-Policy': 'cross-origin',
    'ngrok-skip-browser-warning': 'true',
}

STRIP_HEADERS = ('content-encoding', 'content-length', 'transfer-encoding')


def rewrite_pygbag_html(body, host, base_path):
    """
    Rewrite Pygbag HTML to work through a Flask proxy.

    - Injects <base href="/base_path/">
    - Rewrites absolute URLs to the proxy base.
    - Cleans up double slashes.
    """
    if '<head>' in body:
        body = body.replace('<head>', f'<head>\n<base href="/{base_path}/">\n', 1)
    elif '<html>' in body:
        body = body.replace('<html>', f'<html>\n<head>\n<base href="/{base_path}/">\n</head>\n', 1)

    public_base = f'https://{host}/{base_path}'

    # Replace ALL localhost references (any port) and external CDN
    body = body.replace('https://pygame-web.github.io/', public_base + '/')
    body = body.replace('http://localhost:8000/', public_base + '/')
    body = body.replace('http://localhost:8001/', public_base + '/')
    body = body.replace('http://localhost:8003/', public_base + '/')   # <-- added for aquarium
    body = body.replace('//localhost:8000/', public_base + '/')
    body = body.replace('//localhost:8001/', public_base + '/')
    body = body.replace('//localhost:8003/', public_base + '/')       # <-- added for aquarium

    # Also catch protocol-relative external CDN
    body = body.replace('//pygame-web.github.io/', public_base + '/')

    # Clean up double slashes
    body = re.sub(r'/({base_path})/(/+)'.format(base_path=base_path), r'/\1/', body)

    return body


# ─── ROUTES ─────────────────────────────────────────────────────────────────────

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
        "neural_transfer": 8002,
        "aquarium": 8003   # <-- added
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


# ─── PROXIES ────────────────────────────────────────────────────────────────────

@bp.route('/pygbag/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/pygbag/<path:path>', methods=["GET", "POST"])
def proxy_pygbag(path):
    url = f'http://localhost:8000/{path}'
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    if request.headers.get('X-Forwarded-Proto'):
        headers['X-Forwarded-Proto'] = request.headers['X-Forwarded-Proto']
    else:
        headers['X-Forwarded-Proto'] = 'https' if request.is_secure else 'http'

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )

    content_type = resp.headers.get('Content-Type', '').lower()
    response_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in STRIP_HEADERS
    }
    response_headers.update(COOP_COEP)

    if 'text/html' in content_type:
        body = resp.content.decode('utf-8', errors='replace')
        body = rewrite_pygbag_html(body, request.host, 'pygbag')
        return Response(body, status=resp.status_code, headers=response_headers, content_type='text/html')

    if any(t in content_type for t in ['javascript', 'css', 'json']):
        return Response(resp.content, status=resp.status_code, headers=response_headers, content_type=content_type)

    return Response(
        resp.iter_content(chunk_size=8192),
        status=resp.status_code,
        headers=response_headers
    )


@bp.route('/sablier/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/sablier/<path:path>', methods=["GET", "POST"])
def proxy_sablier(path):
    url = f'http://localhost:8001/{path}'
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    if request.headers.get('X-Forwarded-Proto'):
        headers['X-Forwarded-Proto'] = request.headers['X-Forwarded-Proto']
    else:
        headers['X-Forwarded-Proto'] = 'https' if request.is_secure else 'http'

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )

    content_type = resp.headers.get('Content-Type', '').lower()
    response_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in STRIP_HEADERS
    }
    response_headers.update(COOP_COEP)

    if 'text/html' in content_type:
        body = resp.content.decode('utf-8', errors='replace')
        body = rewrite_pygbag_html(body, request.host, 'sablier')
        return Response(body, status=resp.status_code, headers=response_headers, content_type='text/html')

    if any(t in content_type for t in ['javascript', 'css', 'json']):
        return Response(resp.content, status=resp.status_code, headers=response_headers, content_type=content_type)

    return Response(
        resp.iter_content(chunk_size=8192),
        status=resp.status_code,
        headers=response_headers
    )


@bp.route('/aquarium/', defaults={'path': ''}, methods=["GET", "POST"])
@bp.route('/aquarium/<path:path>', methods=["GET", "POST"])
def proxy_aquarium(path):
    url = f'http://localhost:8003/{path}'
    headers = {k: v for k, v in request.headers if k.lower() != 'host'}

    if request.headers.get('X-Forwarded-Proto'):
        headers['X-Forwarded-Proto'] = request.headers['X-Forwarded-Proto']
    else:
        headers['X-Forwarded-Proto'] = 'https' if request.is_secure else 'http'

    resp = requests.request(
        method=request.method,
        url=url,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        stream=True
    )

    content_type = resp.headers.get('Content-Type', '').lower()
    response_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in STRIP_HEADERS
    }
    response_headers.update(COOP_COEP)

    if 'text/html' in content_type:
        body = resp.content.decode('utf-8', errors='replace')
        body = rewrite_pygbag_html(body, request.host, 'aquarium')
        return Response(body, status=resp.status_code, headers=response_headers, content_type='text/html')

    if any(t in content_type for t in ['javascript', 'css', 'json']):
        return Response(resp.content, status=resp.status_code, headers=response_headers, content_type=content_type)

    return Response(
        resp.iter_content(chunk_size=8192),
        status=resp.status_code,
        headers=response_headers
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