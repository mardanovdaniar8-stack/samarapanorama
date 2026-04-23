import os
import json
import zipfile
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, abort

app = Flask(__name__, static_folder='.', static_url_path='')

ROUTES_DIR = Path('routes')
EXTRACTED_BASE = Path('extracted')

ROUTES_DIR.mkdir(exist_ok=True)
EXTRACTED_BASE.mkdir(exist_ok=True)

def extract_irf(irf_path: Path, route_id: str) -> Path:
    dest = EXTRACTED_BASE / route_id
    if dest.exists():
        return dest
    dest.mkdir(parents=True)
    with zipfile.ZipFile(irf_path, 'r') as zf:
        zf.extractall(dest)
    return dest

def get_route_info(irf_path: Path):
    route_id = irf_path.stem
    with zipfile.ZipFile(irf_path, 'r') as zf:
        metadata = {}
        if 'metadata.json' in zf.namelist():
            with zf.open('metadata.json') as f:
                metadata = json.load(f)
        total_slides = 0
        if 'presentation.json' in zf.namelist():
            with zf.open('presentation.json') as f:
                pres = json.load(f)
                if isinstance(pres, list):
                    total_slides = len(pres)
        return {
            'id': route_id,
            'name': metadata.get('Name') or route_id,
            'desc': metadata.get('Desc') or '',
            'time': metadata.get('Time') or '',
            'pic': metadata.get('Pic') or '',
            'totalSlides': total_slides
        }

def scan_routes():
    routes = []
    for irf_file in ROUTES_DIR.glob('*.irf'):
        try:
            routes.append(get_route_info(irf_file))
        except Exception as e:
            print(f"Ошибка чтения {irf_file}: {e}")
    return routes

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/routes')
def api_routes():
    return jsonify({'routes': scan_routes()})

@app.route('/route/<route_id>/<path:filename>')
def serve_route_file(route_id, filename):
    irf_path = ROUTES_DIR / f"{route_id}.irf"
    if not irf_path.exists():
        abort(404, description="IRF файл не найден")
    dest_dir = extract_irf(irf_path, route_id)
    safe_path = (dest_dir / filename).resolve()
    if not str(safe_path).startswith(str(dest_dir.resolve())):
        abort(403)
    if not safe_path.exists():
        abort(404)
    return send_from_directory(dest_dir, filename)

if __name__ == '__main__':
    print("🚀 Сервер ready: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)