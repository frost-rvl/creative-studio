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
<html>
<head><title>Neural Style Transfer</title>
<style>
    body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
    form { background: #f9f9f9; padding: 2rem; border-radius: 8px; }
    label { display: block; margin-top: 1rem; font-weight: bold; }
    input, select { margin-top: 0.3rem; }
    .result { margin-top: 2rem; text-align: center; }
    .result img { max-width: 100%; max-height: 600px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .error { color: #d32f2f; background: #ffebee; padding: 0.5rem; border-radius: 4px; margin-top: 1rem; }
    button { margin-top: 1.5rem; background: #e53935; color: white; border: none; padding: 0.7rem 2rem; border-radius: 4px; font-size: 1rem; cursor: pointer; }
</style>
</head>
<body>
    <h1>Neural Style Transfer</h1>
    <form method="POST" enctype="multipart/form-data" action="transfer">
        <label for="content">Upload your image:</label>
        <input type="file" name="content" accept="image/*" required>
        <label for="painter">Choose a style:</label>
        <select name="painter" id="painter">
            {% for key, name in painters.items() %}
                <option value="{{ key }}">{{ name }}</option>
            {% endfor %}
        </select>
        <button type="submit">Transform</button>
    </form>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    {% if result_data %}
        <div class="result">
            <h3>Styled result</h3>
            <img src="data:image/jpeg;base64,{{ result_data }}" alt="Styled image">
            <p><small>Style: {{ painter_display }} · Elapsed: {{ elapsed }}s</small></p>
        </div>
    {% endif %}
    <p><a href="./">New transformation</a></p>

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
    </script>
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