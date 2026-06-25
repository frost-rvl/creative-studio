"""
Module 3 — Image Manipulation Lab (single‑file version)
Creative Studio | ENSA Tanger 2025

Run:
    pip install flask pillow opencv-python-headless numpy
    python service.py
Then open http://localhost:8004
"""

import io, base64, uuid
import cv2, numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
from flask import Flask, request, jsonify, send_file, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# ══════════════════════════════════════════════════════════════════
#  IMAGE PROCESSING ENGINE
# ══════════════════════════════════════════════════════════════════

def pil_to_cv(img):
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

def cv_to_pil(arr):
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

def img_to_b64(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# ── Color Filters ──────────────────────────────────────────────
def filter_grayscale(img):
    return ImageOps.grayscale(img).convert("RGB")

def filter_sepia(img):
    g = np.array(ImageOps.grayscale(img).convert("RGB"), dtype=np.float64)
    r = np.clip(g[:,:,0]*0.393 + g[:,:,1]*0.769 + g[:,:,2]*0.189, 0, 255)
    gn= np.clip(g[:,:,0]*0.349 + g[:,:,1]*0.686 + g[:,:,2]*0.168, 0, 255)
    b = np.clip(g[:,:,0]*0.272 + g[:,:,1]*0.534 + g[:,:,2]*0.131, 0, 255)
    return Image.fromarray(np.stack([r,gn,b],2).astype(np.uint8))

def filter_invert(img):
    return ImageOps.invert(img.convert("RGB"))

def filter_neon(img):
    cv = pil_to_cv(img)
    edges = cv2.Canny(cv, 50, 150)
    ec = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    neon = np.zeros_like(cv)
    neon[:,:,1] = ec[:,:,1]
    neon[:,:,0] = (ec[:,:,0]*0.5).astype(np.uint8)
    return cv_to_pil(cv2.addWeighted(cv, 0.4, cv2.GaussianBlur(neon,(7,7),0), 0.9, 0))

def filter_vintage(img):
    w = np.array(ImageEnhance.Color(img.convert("RGB")).enhance(0.6), dtype=np.float32)
    w[:,:,0] = np.clip(w[:,:,0]*1.12, 0, 255)
    w[:,:,2] = np.clip(w[:,:,2]*0.85, 0, 255)
    return Image.fromarray(w.astype(np.uint8))

def filter_cyberpunk(img):
    hsv = cv2.cvtColor(pil_to_cv(img), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:,:,0] = (hsv[:,:,0]+60)%180
    hsv[:,:,1] = np.clip(hsv[:,:,1]*1.8, 0, 255)
    hsv[:,:,2] = np.clip(hsv[:,:,2]*1.1, 0, 255)
    return cv_to_pil(cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR))

# ── Artistic Effects ───────────────────────────────────────────
def effect_glitch(img, intensity=10):
    arr = np.array(img.convert("RGB"))
    h, w = arr[:,:,0].shape
    s = max(1, min(intensity, w//4))
    r = arr.copy()
    r[:,:,0] = np.roll(arr[:,:,0], s, axis=1)
    r[:,:,2] = np.roll(arr[:,:,2], -s, axis=1)
    rng = np.random.default_rng(42)
    for _ in range(intensity*2):
        y = rng.integers(0, h)
        r[y,:,:] = np.roll(r[y,:,:], rng.integers(-s*2, s*2), axis=0)
    return Image.fromarray(r)

def effect_pixelate(img, block_size=16):
    w, h = img.size
    sm = img.resize((max(1,w//block_size), max(1,h//block_size)), Image.NEAREST)
    return sm.resize((w,h), Image.NEAREST)

def effect_watercolor(img):
    cv = pil_to_cv(img)
    for _ in range(3):
        cv = cv2.bilateralFilter(cv, 9, 75, 75)
    return cv_to_pil(cv2.addWeighted(cv, 0.7, cv2.medianBlur(cv,3), 0.3, 0))

def effect_blur(img):
    return img.convert("RGB").filter(ImageFilter.GaussianBlur(radius=5))

def effect_oil_paint(img):
    cv = pil_to_cv(img)
    d = cv2.addWeighted(cv, 1.5, cv2.GaussianBlur(cv,(15,15),0), -0.5, 0)
    for _ in range(2):
        d = cv2.bilateralFilter(d, 11, 80, 80)
    return cv_to_pil(d)

def effect_sketch(img):
    cv = pil_to_cv(img)
    gray = cv2.cvtColor(cv, cv2.COLOR_BGR2GRAY)
    sketch = cv2.divide(gray, cv2.bitwise_not(cv2.GaussianBlur(cv2.bitwise_not(gray),(21,21),0)), scale=256)
    return Image.fromarray(sketch).convert("RGB")

# ── Geometric Transforms ───────────────────────────────────────
def transform_mirror_h(img):  return ImageOps.mirror(img.convert("RGB"))
def transform_mirror_v(img):  return ImageOps.flip(img.convert("RGB"))
def transform_rotate90(img):  return img.convert("RGB").rotate(90, expand=True)
def transform_rotate180(img): return img.convert("RGB").rotate(180, expand=True)

def transform_kaleidoscope(img):
    rgb = img.convert("RGB")
    w, h = rgb.size
    hw, hh = w//2, h//2
    tl = rgb.crop((0,0,hw,hh))
    res = Image.new("RGB",(hw*2,hh*2))
    res.paste(tl,(0,0)); res.paste(ImageOps.mirror(tl),(hw,0))
    bl = ImageOps.flip(tl)
    res.paste(bl,(0,hh)); res.paste(ImageOps.mirror(bl),(hw,hh))
    return res

# ── Edge Detection ─────────────────────────────────────────────
def effect_contour(img):
    cv = pil_to_cv(img)
    edges = cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(cv,cv2.COLOR_BGR2GRAY),(5,5),0),30,120)
    res = np.zeros_like(cv)
    res[edges>0] = [255,255,255]
    return cv_to_pil(res)

def effect_emboss(img):
    return img.convert("RGB").filter(ImageFilter.EMBOSS)

# ── Registry ───────────────────────────────────────────────────
EFFECTS = {
    "grayscale":    (filter_grayscale,     "Color Filter",    "🎞️"),
    "sepia":        (filter_sepia,         "Color Filter",    "🟤"),
    "invert":       (filter_invert,        "Color Filter",    "🔃"),
    "neon":         (filter_neon,          "Color Filter",    "💚"),
    "vintage":      (filter_vintage,       "Color Filter",    "📷"),
    "cyberpunk":    (filter_cyberpunk,     "Color Filter",    "🌆"),
    "glitch":       (effect_glitch,        "Artistic Effect", "⚡"),
    "pixelate":     (effect_pixelate,      "Artistic Effect", "🟦"),
    "watercolor":   (effect_watercolor,    "Artistic Effect", "🎨"),
    "blur":         (effect_blur,          "Artistic Effect", "🌫️"),
    "oil_paint":    (effect_oil_paint,     "Artistic Effect", "🖌️"),
    "sketch":       (effect_sketch,        "Artistic Effect", "✏️"),
    "mirror_h":     (transform_mirror_h,   "Transform",       "↔️"),
    "mirror_v":     (transform_mirror_v,   "Transform",       "↕️"),
    "rotate_90":    (transform_rotate90,   "Transform",       "🔄"),
    "rotate_180":   (transform_rotate180,  "Transform",       "🔁"),
    "kaleidoscope": (transform_kaleidoscope,"Transform",      "🔮"),
    "contour":      (effect_contour,       "Edge Detection",  "🔲"),
    "emboss":       (effect_emboss,        "Edge Detection",  "🗿"),
}

def apply_chain(img, names):
    for name in names:
        if name not in EFFECTS:
            raise ValueError(f"Unknown effect: {name}")
        img = EFFECTS[name][0](img)
    return img

# ══════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    categories = {}
    for key, (_, cat, icon) in EFFECTS.items():
        categories.setdefault(cat, []).append({
            "key": key,
            "label": key.replace("_", " ").title(),
            "icon": icon,
        })
    return render_template_string(HTML, categories=categories)


@app.route("/process", methods=["POST"])
def process():
    effects_raw = request.form.get("effects", "")
    effect_list = [e.strip() for e in effects_raw.split(",") if e.strip()]
    if not effect_list:
        return jsonify({"error": "No effects selected"}), 400

    try:
        if "file" in request.files and request.files["file"].filename:
            img = Image.open(request.files["file"].stream).convert("RGBA")
        elif request.form.get("image_b64"):
            img = Image.open(io.BytesIO(base64.b64decode(request.form["image_b64"]))).convert("RGBA")
        else:
            return jsonify({"error": "No image provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if max(img.size) > 1600:
        img.thumbnail((1600, 1600), Image.LANCZOS)

    try:
        result = apply_chain(img, effect_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "result_b64": img_to_b64(result),
        "width": result.width,
        "height": result.height,
        "applied": effect_list,
    })


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(force=True)
    fmt = data.get("format", "PNG").upper()
    if fmt not in ("PNG", "JPEG", "WEBP"):
        fmt = "PNG"
    img = Image.open(io.BytesIO(base64.b64decode(data["image_b64"]))).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return send_file(buf, mimetype=f"image/{fmt.lower()}",
                     as_attachment=True,
                     download_name=f"creative_studio_{uuid.uuid4().hex[:8]}.{ext}")

# ══════════════════════════════════════════════════════════════════
#  HTML TEMPLATE (inline)
# ══════════════════════════════════════════════════════════════════

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Image Lab — Creative Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet"/>
<style>
:root{--bg:#0a0a0f;--surface:#111118;--surface2:#18181f;--border:rgba(255,255,255,0.08);--accent:#7c5cfc;--accent2:#fc5c7c;--text:#e8e8f0;--text-dim:#6b6b80;--text-xdim:#3a3a50;--mono:'Space Mono',monospace;--sans:'Space Grotesk',sans-serif;--radius:12px;--radius-sm:6px;--radius-pill:999px}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh}
.nav{display:flex;align-items:center;justify-content:space-between;padding:1rem 2rem;border-bottom:1px solid var(--border);position:sticky;top:0;background:rgba(10,10,15,.9);backdrop-filter:blur(12px);z-index:100}
.nav-brand{font-family:var(--mono);font-size:.95rem;color:var(--text);text-decoration:none;letter-spacing:.04em}
.nav-brand:hover{color:var(--accent)}
.nav-tag{font-family:var(--mono);font-size:.75rem;color:var(--text-dim);padding:.25rem .75rem;border:1px solid var(--border);border-radius:var(--radius-pill)}
.hero{padding:4rem 2rem 3rem;max-width:900px;margin:0 auto}
.hero-eyebrow{font-family:var(--mono);font-size:.75rem;letter-spacing:.2em;color:var(--accent);text-transform:uppercase;margin-bottom:1rem}
.hero-title{font-size:clamp(2.8rem,7vw,5.5rem);font-weight:700;line-height:1;letter-spacing:-.03em;margin-bottom:1rem}
.hero-title em{font-style:normal;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.hero-sub{color:var(--text-dim);font-size:1.05rem}
.workspace{max-width:1100px;margin:0 auto;padding:0 2rem 4rem;display:flex;flex-direction:column;gap:2rem}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:1.75rem}
.panel-header{display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem;flex-wrap:wrap}
.panel-num{font-family:var(--mono);font-size:.7rem;color:var(--accent);border:1px solid var(--accent);border-radius:var(--radius-pill);padding:.15rem .5rem;flex-shrink:0}
.panel-header h2{font-size:1.1rem;font-weight:600;flex:1}
.drop-zone{border:2px dashed var(--border);border-radius:var(--radius);min-height:200px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:border-color .2s,background .2s;position:relative;overflow:hidden}
.drop-zone:hover,.drop-zone.dragover{border-color:var(--accent);background:rgba(124,92,252,.04)}
.drop-content{text-align:center;padding:2rem;pointer-events:none}
.drop-icon{font-size:2.5rem;margin-bottom:.75rem;color:var(--text-dim)}
.drop-label{font-size:.95rem;color:var(--text);margin-bottom:.35rem}
.drop-hint{font-family:var(--mono);font-size:.72rem;color:var(--text-dim)}
.link-btn{background:none;border:none;color:var(--accent);cursor:pointer;font-family:inherit;font-size:inherit;text-decoration:underline;pointer-events:all}
.preview-img{width:100%;max-height:320px;object-fit:contain;border-radius:calc(var(--radius) - 2px)}
.upload-meta{display:flex;align-items:center;gap:.75rem;margin-top:.75rem;font-size:.8rem}
.meta-name{font-family:var(--mono);color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:220px}
.meta-dims{font-family:var(--mono);color:var(--text-dim)}
.effects-grid{display:flex;flex-direction:column;gap:1.25rem}
.effect-category{font-family:var(--mono);font-size:.68rem;letter-spacing:.15em;text-transform:uppercase;color:var(--text-dim);margin-bottom:.6rem}
.effect-pills{display:flex;flex-wrap:wrap;gap:.5rem}
.pill{display:inline-flex;align-items:center;gap:.35rem;padding:.45rem .85rem;background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius-pill);color:var(--text-dim);font-family:var(--sans);font-size:.82rem;cursor:pointer;transition:all .15s;user-select:none}
.pill:hover{border-color:var(--accent);color:var(--text)}
.pill.active{background:rgba(124,92,252,.15);border-color:var(--accent);color:var(--accent)}
.pill-icon{font-size:.95rem}.pill-label{line-height:1}
.badge{font-family:var(--mono);font-size:.7rem;padding:.2rem .6rem;background:rgba(124,92,252,.15);border:1px solid var(--accent);border-radius:var(--radius-pill);color:var(--accent);margin-left:auto}
.chain-row{display:flex;align-items:center;gap:.75rem;margin-top:1.25rem;padding-top:1.25rem;border-top:1px solid var(--border)}
.chain-preview{flex:1;display:flex;flex-wrap:wrap;gap:.4rem;min-height:32px;align-items:center}
.chain-empty{font-size:.78rem;color:var(--text-xdim);font-style:italic}
.chain-tag{font-family:var(--mono);font-size:.7rem;padding:.2rem .55rem;background:rgba(252,92,124,.12);border:1px solid rgba(252,92,124,.3);color:var(--accent2);border-radius:var(--radius-pill)}
.canvas-area{display:grid;grid-template-columns:1fr auto 1fr;gap:1rem;align-items:center}
.canvas-slot{display:flex;flex-direction:column;gap:.5rem}
.canvas-label{font-family:var(--mono);font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--text-dim)}
.canvas-placeholder{aspect-ratio:4/3;background:var(--surface2);border:1px dashed var(--border);border-radius:var(--radius);display:flex;align-items:center;justify-content:center;text-align:center;color:var(--text-xdim);font-size:.82rem;line-height:1.6}
.canvas-img{width:100%;border-radius:var(--radius);object-fit:contain;max-height:420px;background:var(--surface2)}
.canvas-divider{display:flex;flex-direction:column;align-items:center;gap:.75rem}
.divider-line{width:1px;height:40px;background:var(--border)}
.btn-apply{width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;color:#fff;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:opacity .2s,transform .2s;flex-shrink:0}
.btn-apply:hover:not(:disabled){transform:scale(1.08)}
.btn-apply:disabled{opacity:.35;cursor:not-allowed}
.result-actions{display:flex;align-items:center;gap:.5rem;margin-left:auto}
.download-group{display:flex;align-items:center;gap:.4rem}
.fmt-select{background:var(--surface2);border:1px solid var(--border);color:var(--text);border-radius:var(--radius-sm);padding:.3rem .5rem;font-family:var(--mono);font-size:.75rem;cursor:pointer}
.history-section{margin-top:1.5rem;padding-top:1.25rem;border-top:1px solid var(--border)}
.history-label{font-family:var(--mono);font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;color:var(--text-dim);margin-bottom:.75rem}
.history-strip{display:flex;gap:.6rem;overflow-x:auto;padding-bottom:.5rem}
.history-thumb{flex-shrink:0;width:72px;height:72px;border-radius:var(--radius-sm);object-fit:cover;cursor:pointer;border:2px solid transparent;transition:border-color .2s;opacity:.7}
.history-thumb:hover{border-color:var(--accent);opacity:1}
.history-thumb.current{border-color:var(--accent2);opacity:1}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--accent2));border:none;color:#fff;border-radius:var(--radius-sm);padding:.45rem 1rem;font-family:var(--sans);font-weight:600;font-size:.82rem;cursor:pointer;transition:opacity .2s}
.btn-primary:hover{opacity:.88}
.btn-ghost{background:transparent;border:1px solid var(--border);color:var(--text-dim);border-radius:var(--radius-sm);padding:.4rem .9rem;font-family:var(--sans);font-size:.8rem;cursor:pointer;transition:border-color .15s,color .15s}
.btn-ghost:hover{border-color:var(--text-dim);color:var(--text)}
.btn-sm{padding:.3rem .7rem;font-size:.77rem}
.spinner{width:18px;height:18px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}
.footer{text-align:center;padding:2rem;border-top:1px solid var(--border);font-size:.75rem;color:var(--text-xdim);font-family:var(--mono)}
.hidden{display:none!important}
@media(max-width:720px){.canvas-area{grid-template-columns:1fr}.canvas-divider{flex-direction:row}.divider-line{width:40px;height:1px}.hero-title{font-size:2.8rem}.workspace{padding:0 1rem 3rem}.panel{padding:1.25rem}}
</style>
</head>
<body>
<nav class="nav">
  <a href="/" class="nav-brand">✦ Creative Studio</a>
  <span class="nav-tag">Module 3 — Image Lab</span>
</nav>

<header class="hero">
  <div class="hero-inner">
    <p class="hero-eyebrow">Transform · Distort · Express</p>
    <h1 class="hero-title">Image<br><em>Manipulation</em></h1>
    <p class="hero-sub">Upload any image. Chain effects. Download your artwork.</p>
  </div>
</header>

<main class="workspace">

  <section class="panel">
    <div class="panel-header">
      <span class="panel-num">01</span>
      <h2>Upload Image</h2>
    </div>
    <div class="drop-zone" id="dropZone">
      <input type="file" id="fileInput" accept="image/*" hidden/>
      <div class="drop-content" id="dropContent">
        <div class="drop-icon">⬆</div>
        <p class="drop-label">Drag & drop or <button class="link-btn" onclick="document.getElementById('fileInput').click()">browse</button></p>
        <p class="drop-hint">PNG · JPG · WEBP · GIF — max 10 MB</p>
      </div>
      <img id="previewImg" class="preview-img hidden" alt="Preview"/>
    </div>
    <div class="upload-meta hidden" id="uploadMeta">
      <span id="metaName" class="meta-name"></span>
      <span id="metaDims" class="meta-dims"></span>
      <button class="btn-ghost btn-sm" id="clearBtn">✕ Clear</button>
    </div>
  </section>

  <section class="panel">
    <div class="panel-header">
      <span class="panel-num">02</span>
      <h2>Select Effects</h2>
      <span class="badge" id="countBadge">0 selected</span>
    </div>
    <div class="effects-grid">
      {% for category, effects in categories.items() %}
      <div class="effect-group">
        <h3 class="effect-category">{{ category }}</h3>
        <div class="effect-pills">
          {% for fx in effects %}
          <button class="pill" data-key="{{ fx.key }}" onclick="toggleEffect(this)">
            <span class="pill-icon">{{ fx.icon }}</span>
            <span class="pill-label">{{ fx.label }}</span>
          </button>
          {% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>
    <div class="chain-row">
      <div class="chain-preview" id="chainPreview"><span class="chain-empty">No effects selected yet</span></div>
      <button class="btn-ghost btn-sm" onclick="clearEffects()">Clear all</button>
    </div>
  </section>

  <section class="panel">
    <div class="panel-header">
      <span class="panel-num">03</span>
      <h2>Result</h2>
      <div class="result-actions hidden" id="resultActions">
        <button class="btn-ghost btn-sm" onclick="undoLast()">↩ Undo</button>
        <div class="download-group">
          <select class="fmt-select" id="fmtSelect">
            <option value="PNG">PNG</option>
            <option value="JPEG">JPEG</option>
            <option value="WEBP">WEBP</option>
          </select>
          <button class="btn-primary btn-sm" onclick="downloadResult()">⬇ Download</button>
        </div>
      </div>
    </div>
    <div class="canvas-area">
      <div class="canvas-slot">
        <p class="canvas-label">Original</p>
        <div class="canvas-placeholder" id="origPlaceholder"><span>Upload an image<br>to get started</span></div>
        <img id="origImg" class="canvas-img hidden" alt="Original"/>
      </div>
      <div class="canvas-divider">
        <div class="divider-line"></div>
        <button class="btn-apply" id="applyBtn" onclick="applyEffects()" disabled>
          <span id="applyBtnText">→</span>
          <span id="applySpinner" class="spinner hidden"></span>
        </button>
        <div class="divider-line"></div>
      </div>
      <div class="canvas-slot">
        <p class="canvas-label">Output</p>
        <div class="canvas-placeholder" id="resultPlaceholder"><span>Output will<br>appear here</span></div>
        <img id="resultImg" class="canvas-img hidden" alt="Result"/>
      </div>
    </div>
    <div class="history-section hidden" id="historySection">
      <p class="history-label">History</p>
      <div class="history-strip" id="historyStrip"></div>
    </div>
  </section>

</main>

<footer class="footer">
  <p>Module 3 · Image Manipulation · Digital Creativity using Python · ENSA Tanger 2025</p>
</footer>

<script>
const state = { originalFile:null, originalB64:null, currentB64:null, selectedEffects:[], history:[] };

const fileInput=document.getElementById("fileInput"),dropZone=document.getElementById("dropZone"),
  dropContent=document.getElementById("dropContent"),previewImg=document.getElementById("previewImg"),
  uploadMeta=document.getElementById("uploadMeta"),metaName=document.getElementById("metaName"),
  metaDims=document.getElementById("metaDims"),clearBtn=document.getElementById("clearBtn"),
  countBadge=document.getElementById("countBadge"),chainPreview=document.getElementById("chainPreview"),
  applyBtn=document.getElementById("applyBtn"),applyBtnText=document.getElementById("applyBtnText"),
  applySpinner=document.getElementById("applySpinner"),origImg=document.getElementById("origImg"),
  origPlaceholder=document.getElementById("origPlaceholder"),resultImg=document.getElementById("resultImg"),
  resultPlaceholder=document.getElementById("resultPlaceholder"),resultActions=document.getElementById("resultActions"),
  historySection=document.getElementById("historySection"),historyStrip=document.getElementById("historyStrip");

dropZone.addEventListener("click",e=>{if(e.target!==fileInput)fileInput.click()});
dropZone.addEventListener("dragover",e=>{e.preventDefault();dropZone.classList.add("dragover")});
dropZone.addEventListener("dragleave",()=>dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop",e=>{e.preventDefault();dropZone.classList.remove("dragover");if(e.dataTransfer.files[0])handleFile(e.dataTransfer.files[0])});
fileInput.addEventListener("change",()=>{if(fileInput.files[0])handleFile(fileInput.files[0])});
clearBtn.addEventListener("click",clearAll);

function handleFile(file){
  if(!file.type.startsWith("image/")){alert("Please upload an image file.");return}
  if(file.size>10*1024*1024){alert("File too large — max 10 MB.");return}
  state.originalFile=file; state.currentB64=null; state.history=[];
  const reader=new FileReader();
  reader.onload=ev=>{
    const url=ev.target.result;
    previewImg.src=url; previewImg.classList.remove("hidden"); dropContent.classList.add("hidden");
    origImg.src=url; origImg.classList.remove("hidden"); origPlaceholder.classList.add("hidden");
    const tmp=new Image(); tmp.onload=()=>{metaDims.textContent=tmp.naturalWidth+" × "+tmp.naturalHeight; state.originalB64=url.split(",")[1]}; tmp.src=url;
    metaName.textContent=file.name; uploadMeta.classList.remove("hidden");
    resultImg.classList.add("hidden"); resultPlaceholder.classList.remove("hidden");
    resultActions.classList.add("hidden"); historySection.classList.add("hidden"); historyStrip.innerHTML="";
    updateApplyBtn();
  };
  reader.readAsDataURL(file);
}

function clearAll(){
  state.originalFile=null; state.originalB64=null; state.currentB64=null; state.history=[];
  state.selectedEffects=[];
  fileInput.value=""; previewImg.classList.add("hidden"); previewImg.src="";
  dropContent.classList.remove("hidden"); uploadMeta.classList.add("hidden");
  origImg.classList.add("hidden"); origImg.src=""; origPlaceholder.classList.remove("hidden");
  resultImg.classList.add("hidden"); resultImg.src=""; resultPlaceholder.classList.remove("hidden");
  resultActions.classList.add("hidden"); historySection.classList.add("hidden"); historyStrip.innerHTML="";
  document.querySelectorAll(".pill.active").forEach(p=>p.classList.remove("active"));
  updateChain(); updateApplyBtn();
}

window.toggleEffect=function(btn){
  const key=btn.dataset.key; btn.classList.toggle("active");
  if(btn.classList.contains("active")) state.selectedEffects.push(key);
  else state.selectedEffects=state.selectedEffects.filter(k=>k!==key);
  updateChain(); updateApplyBtn();
};

window.clearEffects=function(){
  state.selectedEffects=[];
  document.querySelectorAll(".pill.active").forEach(p=>p.classList.remove("active"));
  updateChain(); updateApplyBtn();
};

function updateChain(){
  countBadge.textContent=state.selectedEffects.length+" selected";
  chainPreview.innerHTML=state.selectedEffects.length===0
    ? '<span class="chain-empty">No effects selected yet</span>'
    : state.selectedEffects.map(k=>`<span class="chain-tag">${k.replace("_"," ")}</span>`).join("");
}

function updateApplyBtn(){applyBtn.disabled=!state.originalFile||state.selectedEffects.length===0}

window.applyEffects=async function(){
  if(!state.originalFile||state.selectedEffects.length===0)return;
  setLoading(true);
  const fd=new FormData();
  fd.append("effects",state.selectedEffects.join(","));
  if(state.currentB64) fd.append("image_b64",state.currentB64);
  else fd.append("file",state.originalFile);
  try{
    const resp=await fetch("process",{method:"POST",body:fd});
    const data=await resp.json();
    if(!resp.ok||data.error){alert("Error: "+(data.error||"Unknown"));return}
    // Store history before applying new state
    state.history.push({
      b64: state.currentB64 || state.originalB64,
      effects: [...state.selectedEffects]
    });
    addHistoryThumb(state.history[state.history.length-1].b64);
    state.currentB64=data.result_b64;
    resultImg.src="data:image/png;base64,"+data.result_b64;
    resultImg.classList.remove("hidden"); resultPlaceholder.classList.add("hidden");
    resultActions.classList.remove("hidden"); historySection.classList.remove("hidden");
    document.querySelectorAll(".history-thumb").forEach(t=>t.classList.remove("current"));
    const last=historyStrip.querySelector(".history-thumb:last-child"); if(last)last.classList.add("current");
  }catch(err){alert("Network error: "+err.message)}
  finally{setLoading(false)}
};

function setLoading(on){applyBtn.disabled=on;applyBtnText.classList.toggle("hidden",on);applySpinner.classList.toggle("hidden",!on)}

window.undoLast=function(){
  if(!state.history.length)return;
  const prev=state.history.pop();
  state.currentB64=prev.b64;
  resultImg.src="data:image/png;base64,"+prev.b64;
  // Remove last applied effect from selectedEffects and uncheck its pill
  if (prev.effects && prev.effects.length) {
    const lastEffect = prev.effects[prev.effects.length - 1];
    state.selectedEffects = state.selectedEffects.filter(k => k !== lastEffect);
    const pill = document.querySelector(`.pill[data-key="${lastEffect}"]`);
    if (pill) pill.classList.remove('active');
  }
  // Remove the last history thumbnail
  const thumbs = historyStrip.querySelectorAll(".history-thumb");
  if (thumbs.length) thumbs[thumbs.length-1].remove();
  // Update UI
  updateChain();
  updateApplyBtn();
  if (!state.history.length) {
    historySection.classList.add("hidden");
    state.currentB64=null;
    resultImg.classList.add("hidden");
    resultPlaceholder.classList.remove("hidden");
    resultActions.classList.add("hidden");
  }
};

function addHistoryThumb(b64){
  const img=document.createElement("img");
  img.src="data:image/png;base64,"+b64; img.className="history-thumb"; img.title="Click to restore";
  img.addEventListener("click",()=>{state.currentB64=b64;resultImg.src="data:image/png;base64,"+b64;resultImg.classList.remove("hidden");resultPlaceholder.classList.add("hidden");document.querySelectorAll(".history-thumb").forEach(t=>t.classList.remove("current"));img.classList.add("current")});
  historyStrip.appendChild(img);
}

window.downloadResult=async function(){
  if(!state.currentB64)return;
  const fmt=document.getElementById("fmtSelect").value;
  try{
    const resp=await fetch("download",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({image_b64:state.currentB64,format:fmt})});
    if(!resp.ok){alert("Download failed");return}
    const blob=await resp.blob(); const url=URL.createObjectURL(blob);
    const a=document.createElement("a"); a.href=url;
    const cd=resp.headers.get("Content-Disposition")||""; const m=cd.match(/filename="?([^"]+)"?/);
    a.download=m?m[1]:"creative_studio."+fmt.toLowerCase(); a.click(); URL.revokeObjectURL(url);
  }catch(err){alert("Download error: "+err.message)}
};

// ----- Expose current processed image to parent page -----
window.getProcessedImage = function() {
    return state.currentB64 || null;
};
console.log("✅ getProcessedImage exposed");
</script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004, debug=False)