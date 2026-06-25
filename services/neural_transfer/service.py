#!/usr/bin/env python3
"""
Neural Style Transfer – Flask API (in‑memory, no persistent storage).
Run: python service.py
Port: 8002
"""

import sys
import types
import tempfile
import os
import base64
from pathlib import Path

# ── Monkey‑patch pkg_resources for Python 3.12+ ──────────────────────────────
if 'pkg_resources' not in sys.modules:
    pkg_resources = types.ModuleType('pkg_resources')
    pkg_resources.parse_version = lambda x: x
    sys.modules['pkg_resources'] = pkg_resources

# ── Add current directory to sys.path ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── Flask ──────────────────────────────────────────────────────────────────────
from flask import Flask, request, render_template_string, jsonify

# ── Style transfer engine ──────────────────────────────────────────────────────
from style_transfer.style_transfer import StyleTransferEngine, PAINTER_DISPLAY_NAMES
from utils.image_utils import validate_image_file, preprocess_image, ImageValidationError

# ── App setup ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # 12 MB

# ── Load the model (once) ──────────────────────────────────────────────────────
print("Loading style transfer model...")
engine = StyleTransferEngine()
print("Model loaded.")

# ── HTML form with JavaScript to expose getStyledImage ──────────────────────
HTML_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Style Transfer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: #f8f9fa;
            color: #1e293b;
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { font-size: 2.5rem; font-weight: 600; color: #0f172a; margin-bottom: 0.5rem; }
        .sub { color: #64748b; margin-bottom: 2rem; }
        .panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        label { display: block; font-size: 0.85rem; font-weight: 500; color: #475569; margin-bottom: 0.3rem; }
        input, select {
            width: 100%;
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.6rem 0.8rem;
            color: #1e293b;
            font-family: inherit;
            font-size: 0.9rem;
            transition: border-color 0.15s;
        }
        input:focus, select:focus { outline: none; border-color: #e53e3e; }
        .btn {
            background: #e53e3e;
            border: none;
            color: white;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s;
            font-family: inherit;
            font-size: 0.9rem;
        }
        .btn:hover { background: #c53030; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .flex { display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap; }
        .mt-2 { margin-top: 1rem; }
        .result-box {
            margin-top: 1.5rem;
            text-align: center;
        }
        .result-box img {
            max-width: 100%;
            max-height: 600px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }
        .result-box .caption {
            margin-top: 0.5rem;
            color: #64748b;
            font-size: 0.85rem;
        }
        .error {
            color: #e53e3e;
            background: #fee2e2;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }
        .text-muted { color: #94a3b8; font-size: 0.85rem; }
        .link { color: #e53e3e; text-decoration: none; font-weight: 500; }
        .link:hover { text-decoration: underline; }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #e2e8f0;
            border-top-color: #e53e3e;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .hidden { display: none !important; }
    </style>
</head>
<body>
<div class="container">
    <h1>Neural Style Transfer</h1>
    <p class="sub">Transform your image using the style of famous painters.</p>

    <div class="panel">
        <form method="POST" enctype="multipart/form-data" action="transfer">
            <div style="margin-bottom: 1.5rem;">
                <label for="content">Upload your image</label>
                <input type="file" name="content" id="content" accept="image/*" required>
            </div>
            <div style="margin-bottom: 1.5rem;">
                <label for="painter">Choose a style</label>
                <select name="painter" id="painter">
                    {% for key, name in painters.items() %}
                        <option value="{{ key }}">{{ name }}</option>
                    {% endfor %}
                </select>
            </div>
            <button type="submit" class="btn" id="submitBtn">Transform</button>
        </form>
    </div>

    {% if error %}
        <div class="panel error">{{ error }}</div>
    {% endif %}

    {% if result_data %}
        <div class="panel result-box">
            <h3 style="font-weight: 500; margin-bottom: 0.75rem;">Styled result</h3>
            <img src="data:image/jpeg;base64,{{ result_data }}" alt="Styled image">
            <div class="caption">Style: {{ painter_display }} · Elapsed: {{ elapsed }}s</div>
        </div>
        <div style="text-align: center;">
            <a href="./" class="link">New transformation</a>
        </div>
    {% else %}
        <div class="panel" style="text-align: center; color: #94a3b8;">
            Upload an image and click "Transform" to see the result here.
        </div>
    {% endif %}

    <script>
        (function() {
            var storedImage = "{{ result_data if result_data else '' }}";
            if (storedImage) {
                window._lastStyledImage = storedImage;
            }
            window.getStyledImage = function() {
                return window._lastStyledImage || null;
            };
            console.log('getStyledImage available');
        })();

        // Optional: loading state
        document.getElementById('submitBtn').addEventListener('click', function() {
            this.disabled = true;
            this.textContent = 'Processing...';
            this.form.submit();
        });
    </script>
</div>
</body>
</html>
"""

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(
        HTML_FORM,
        painters=PAINTER_DISPLAY_NAMES,
        error=None,
        result_data=None,
        painter_display=None,
        elapsed=None
    )

@app.route("/transfer", methods=["POST"])
def transfer():
    try:
        if "content" not in request.files:
            return render_template_string(
                HTML_FORM, painters=PAINTER_DISPLAY_NAMES,
                error="No file uploaded."
            ), 400

        file = request.files["content"]
        if file.filename == "":
            return render_template_string(
                HTML_FORM, painters=PAINTER_DISPLAY_NAMES,
                error="Empty filename."
            ), 400

        painter = request.form.get("painter")
        if painter not in PAINTER_DISPLAY_NAMES:
            return render_template_string(
                HTML_FORM, painters=PAINTER_DISPLAY_NAMES,
                error=f"Invalid painter. Choose from {list(PAINTER_DISPLAY_NAMES.keys())}"
            ), 400

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = os.path.join(tmpdir, file.filename)
            file.save(tmp_path)

            try:
                validate_image_file(tmp_path)
                processed_path = preprocess_image(tmp_path, max_dim=1024)

                result = engine.transfer(processed_path, painter)

                with open(result["output_path"], "rb") as f:
                    image_data = f.read()

                b64 = base64.b64encode(image_data).decode('utf-8')

                os.unlink(result["output_path"])

                if request.headers.get("Accept") == "application/json":
                    return jsonify({
                        "image": b64,
                        "painter": painter,
                        "display_name": result["display_name"],
                        "elapsed": result["elapsed_sec"]
                    })

                return render_template_string(
                    HTML_FORM,
                    painters=PAINTER_DISPLAY_NAMES,
                    result_data=b64,
                    painter_display=result["display_name"],
                    elapsed=result["elapsed_sec"],
                    error=None
                )

            except ImageValidationError as e:
                return render_template_string(
                    HTML_FORM, painters=PAINTER_DISPLAY_NAMES,
                    error=str(e)
                ), 400
            except Exception as e:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template_string(
            HTML_FORM, painters=PAINTER_DISPLAY_NAMES,
            error=f"Internal error: {str(e)}"
        ), 500

# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8002, debug=False)