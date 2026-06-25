"""
Data Visualization Lab — Creative Studio
Turn any dataset into an artistic visualization.

Run:
    pip install flask pandas matplotlib numpy
    python service.py
Then open http://localhost:8005
"""

import io
import base64
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# ─── Global state ──────────────────────────────────────────────
last_image_b64 = None
df_global = None

# ─── HTML Template ──────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Visualization Lab</title>
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
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-size: 2.5rem; font-weight: 600; color: #0f172a; margin-bottom: 0.5rem; }
        .sub { color: #64748b; margin-bottom: 2rem; }
        .panel {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        label { display: block; font-size: 0.85rem; font-weight: 500; color: #475569; margin-bottom: 0.3rem; }
        input, select, textarea {
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
        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #e53e3e;
        }
        .btn {
            background: #e53e3e;
            border: none;
            color: white;
            padding: 0.6rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s;
        }
        .btn:hover { background: #c53030; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .flex { display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap; }
        .mt-2 { margin-top: 1rem; }
        .preview-table {
            overflow-x: auto;
            max-height: 250px;
            display: block;
            font-size: 0.8rem;
        }
        .preview-table table { border-collapse: collapse; width: 100%; }
        .preview-table th, .preview-table td {
            padding: 0.3rem 0.6rem;
            border: 1px solid #e2e8f0;
            text-align: left;
        }
        .preview-table th { background: #f1f5f9; color: #1e293b; font-weight: 600; }
        .result-img { width: 100%; border-radius: 8px; margin-top: 1rem; border: 1px solid #e2e8f0; }
        .hidden { display: none !important; }
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
        .badge {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            padding: 0.15rem 0.6rem;
            font-size: 0.7rem;
            color: #475569;
        }
        .error-msg { color: #e53e3e; background: #fee2e2; padding: 0.5rem 1rem; border-radius: 8px; margin-top: 0.5rem; }
        .text-muted { color: #94a3b8; font-size: 0.85rem; }
        @media (max-width: 768px) { .grid-2 { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<div class="container">
    <h1>Data Visualization Lab</h1>
    <p class="sub">Upload a CSV dataset, choose columns, and generate an artistic visualization.</p>

    <div class="panel">
        <div class="grid-2">
            <div>
                <label for="fileUpload">Upload CSV</label>
                <input type="file" id="fileUpload" accept=".csv">
                <div class="mt-2 flex">
                    <button class="btn" id="loadBtn">Load Data</button>
                    <span id="loadStatus" class="text-muted"></span>
                </div>
            </div>
            <div>
                <label for="vizType">Visualization Type</label>
                <select id="vizType">
                    <option value="artistic_heatmap">Artistic Heatmap (hexbin)</option>
                    <option value="wave_landscape">Wave Landscape</option>
                    <option value="abstract_bars">Abstract Bars</option>
                    <option value="scatter_art">Scatter Art</option>
                    <option value="rainbow_lines">Rainbow Lines</option>
                </select>
                <div class="grid-2 mt-2" style="grid-template-columns: 1fr 1fr; gap:0.8rem;">
                    <div>
                        <label for="xCol">X Column</label>
                        <select id="xCol"><option value="">—</option></select>
                    </div>
                    <div>
                        <label for="yCol">Y Column</label>
                        <select id="yCol"><option value="">—</option></select>
                    </div>
                    <div>
                        <label for="cCol">Color Column (optional, numeric)</label>
                        <select id="cCol"><option value="">—</option></select>
                    </div>
                    <div>
                        <label for="gridSize">Grid / Detail</label>
                        <input type="number" id="gridSize" value="40" min="5" max="100">
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="panel">
        <div class="flex" style="justify-content:space-between;">
            <span><strong>Data Preview</strong> <span class="badge" id="shapeInfo">—</span></span>
            <span class="text-muted">First 5 rows</span>
        </div>
        <div class="preview-table" id="previewContainer"><p class="text-muted">No data loaded.</p></div>
    </div>

    <div class="panel">
        <div class="flex" style="justify-content:space-between;">
            <span><strong>Artwork</strong></span>
            <button class="btn" id="generateBtn">Generate</button>
        </div>
        <div id="resultArea">
            <img id="resultImg" class="result-img hidden" alt="Visualization">
            <div id="loadingIndicator" class="hidden" style="text-align:center; padding:2rem;">
                <div class="spinner"></div>
                <p class="text-muted" style="margin-top:0.5rem;">Generating artwork...</p>
            </div>
            <div id="noDataMsg" class="text-muted" style="padding:2rem; text-align:center;">
                Upload a CSV and click "Generate".
            </div>
            <div id="errorMsg" class="error-msg hidden"></div>
        </div>
    </div>
</div>

<script>
let columns = [];
let currentImageB64 = null;
let errorMsg = document.getElementById('errorMsg');

const fileInput = document.getElementById('fileUpload');
const loadBtn = document.getElementById('loadBtn');
const loadStatus = document.getElementById('loadStatus');
const vizType = document.getElementById('vizType');
const xCol = document.getElementById('xCol');
const yCol = document.getElementById('yCol');
const cCol = document.getElementById('cCol');
const gridSize = document.getElementById('gridSize');
const generateBtn = document.getElementById('generateBtn');
const resultImg = document.getElementById('resultImg');
const loadingIndicator = document.getElementById('loadingIndicator');
const noDataMsg = document.getElementById('noDataMsg');
const previewContainer = document.getElementById('previewContainer');
const shapeInfo = document.getElementById('shapeInfo');

loadBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) { alert('Please select a CSV file.'); return; }
    const formData = new FormData();
    formData.append('file', file);
    loadStatus.textContent = 'Loading...';
    loadBtn.disabled = true;
    errorMsg.classList.add('hidden');
    try {
        const resp = await fetch('upload', { method: 'POST', body: formData });
        const data = await resp.json();
        if (!resp.ok) { alert('Error: ' + data.error); return; }
        columns = data.columns;
        shapeInfo.textContent = data.shape;
        [xCol, yCol, cCol].forEach(sel => {
            sel.innerHTML = '<option value="">—</option>';
            columns.forEach(col => {
                const opt = document.createElement('option');
                opt.value = col;
                opt.textContent = col;
                sel.appendChild(opt);
            });
        });
        const numericCols = data.numeric || [];
        if (numericCols.length >= 2) {
            xCol.value = numericCols[0];
            yCol.value = numericCols[1];
        } else if (columns.length >= 2) {
            xCol.value = columns[0];
            yCol.value = columns[1];
        }
        renderPreview(data.preview);
        loadStatus.textContent = `✅ ${data.rows} rows loaded`;
    } catch (err) {
        alert('Error: ' + err.message);
        loadStatus.textContent = '❌ Error';
    }
    loadBtn.disabled = false;
});

function renderPreview(rows) {
    if (!rows || rows.length === 0) {
        previewContainer.innerHTML = '<p class="text-muted">No data to preview.</p>';
        return;
    }
    const cols = Object.keys(rows[0]);
    let html = '<table><thead><tr>';
    cols.forEach(c => html += `<th>${c}</th>`);
    html += '</tr></thead><tbody>';
    rows.forEach(row => {
        html += '<tr>';
        cols.forEach(c => html += `<td>${row[c]}</td>`);
        html += '</tr>';
    });
    html += '</tbody></table>';
    previewContainer.innerHTML = html;
}

generateBtn.addEventListener('click', async () => {
    const x = xCol.value;
    const y = yCol.value;
    const c = cCol.value || '';
    const viz = vizType.value;
    const gs = parseInt(gridSize.value) || 40;
    if (!x || !y) {
        alert('Please select X and Y columns.');
        return;
    }
    loadingIndicator.classList.remove('hidden');
    noDataMsg.classList.add('hidden');
    resultImg.classList.add('hidden');
    errorMsg.classList.add('hidden');
    generateBtn.disabled = true;

    const payload = { x, y, color: c, viz, grid_size: gs };
    try {
        const resp = await fetch('generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (!resp.ok) {
            errorMsg.textContent = '❌ ' + (data.error || 'Unknown error');
            errorMsg.classList.remove('hidden');
            return;
        }
        currentImageB64 = data.image;
        resultImg.src = 'data:image/png;base64,' + data.image;
        resultImg.classList.remove('hidden');
    } catch (err) {
        errorMsg.textContent = '❌ Network error: ' + err.message;
        errorMsg.classList.remove('hidden');
    } finally {
        loadingIndicator.classList.add('hidden');
        generateBtn.disabled = false;
    }
});

window.getVisualization = function() {
    return currentImageB64 || null;
};
console.log('getVisualization exposed');
</script>
</body>
</html>
"""

# ─── Flask routes ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    global df_global
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    try:
        df = pd.read_csv(file.stream)
        if df.empty:
            return jsonify({'error': 'Empty CSV'}), 400
        df_global = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        preview = df.head(5).to_dict(orient='records')
        return jsonify({
            'columns': df.columns.tolist(),
            'numeric': numeric_cols,
            'shape': f'{df.shape[0]} rows × {df.shape[1]} cols',
            'rows': len(df),
            'preview': preview
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    global df_global, last_image_b64
    if df_global is None or df_global.empty:
        return jsonify({'error': 'No data loaded'}), 400
    data = request.json
    x_col = data.get('x')
    y_col = data.get('y')
    color_col = data.get('color') or None
    viz_type = data.get('viz', 'artistic_heatmap')
    grid_size = data.get('grid_size', 40)

    # Validate columns exist
    for col in [x_col, y_col]:
        if col not in df_global.columns:
            return jsonify({'error': f'Column "{col}" not found'}), 400
    if color_col and color_col not in df_global.columns:
        return jsonify({'error': f'Column "{color_col}" not found'}), 400

    # Validate numeric type for color column
    if color_col and not np.issubdtype(df_global[color_col].dtype, np.number):
        return jsonify({'error': f'Column "{color_col}" must be numeric for color mapping'}), 400

    df = df_global.dropna(subset=[x_col, y_col])
    if len(df) < 2:
        return jsonify({'error': 'Not enough valid data points'}), 400

    fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
    cmap = plt.cm.viridis

    try:
        if viz_type == 'artistic_heatmap':
            x_vals = df[x_col]
            y_vals = df[y_col]
            if color_col:
                c_vals = df[color_col]
            else:
                c_vals = np.ones(len(df))
            ax.hexbin(x_vals, y_vals, C=c_vals, gridsize=grid_size,
                      reduce_C_function=np.mean, cmap=cmap, alpha=0.85)
            ax.axis('off')
            plt.title('Artistic Heatmap', fontsize=14, pad=20)

        elif viz_type == 'wave_landscape':
            df_sorted = df.sort_values(by=x_col)
            x_vals = df_sorted[x_col]
            y_vals = df_sorted[y_col]
            ax.fill_between(x_vals, y_vals, y_vals.min() - 5,
                            color='#7c5cfc', alpha=0.3)
            ax.plot(x_vals, y_vals, color='#fc5c7c', linewidth=2)
            ax.set_facecolor('#0a0a0f')
            ax.grid(alpha=0.1)
            ax.set_xlabel(x_col, color='#6b6b80')
            ax.set_ylabel(y_col, color='#6b6b80')
            ax.set_title('Wave Landscape', fontsize=14, pad=20)

        elif viz_type == 'abstract_bars':
            bars = df.sort_values(by=x_col)[:50]
            x_vals = bars[x_col]
            y_vals = bars[y_col]
            colors = plt.cm.plasma(np.linspace(0, 1, len(y_vals)))
            ax.bar(x_vals.astype(str), y_vals, color=colors, alpha=0.8)
            ax.tick_params(axis='x', rotation=45)
            ax.set_xlabel(x_col, color='#6b6b80')
            ax.set_ylabel(y_col, color='#6b6b80')
            ax.set_title('Abstract Bars', fontsize=14, pad=20)

        elif viz_type == 'scatter_art':
            x_vals = df[x_col]
            y_vals = df[y_col]
            sizes = (df[color_col] if color_col else np.ones(len(df))) * 10
            colors = plt.cm.rainbow(np.linspace(0, 1, len(df)))
            ax.scatter(x_vals, y_vals, s=sizes, c=colors, alpha=0.6,
                       edgecolors='white', linewidth=0.3)
            ax.set_xlabel(x_col, color='#6b6b80')
            ax.set_ylabel(y_col, color='#6b6b80')
            ax.set_title('Scatter Art', fontsize=14, pad=20)

        elif viz_type == 'rainbow_lines':
            if len(df.columns) < 3:
                return jsonify({'error': 'Need at least 3 columns for rainbow lines'}), 400
            df_sorted = df.sort_values(by=x_col)
            num_cols = [c for c in df_sorted.columns if c != x_col and np.issubdtype(df_sorted[c].dtype, np.number)][:5]
            if not num_cols:
                return jsonify({'error': 'No numeric columns for lines'}), 400
            for i, col in enumerate(num_cols):
                ax.plot(df_sorted[x_col], df_sorted[col],
                        color=plt.cm.rainbow(i / len(num_cols)),
                        linewidth=2, alpha=0.7, label=col)
            ax.legend(loc='upper left', framealpha=0.3)
            ax.set_xlabel(x_col, color='#6b6b80')
            ax.set_title('Rainbow Lines', fontsize=14, pad=20)

        else:
            return jsonify({'error': f'Unknown visualization type: {viz_type}'}), 400

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        last_image_b64 = img_b64
        return jsonify({'image': img_b64})

    except Exception as e:
        plt.close(fig)
        return jsonify({'error': str(e)}), 500

# ─── Run ────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=False)