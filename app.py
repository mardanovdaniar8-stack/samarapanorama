import os
import json
import zipfile
import hashlib
import secrets
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, abort, request, session

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

ROUTES_DIR = Path('routes')
EXTRACTED_BASE = Path('extracted')
USERS_FILE = Path('users.json')
VERIFICATION_CODE = '676767'

ROUTES_DIR.mkdir(exist_ok=True)
EXTRACTED_BASE.mkdir(exist_ok=True)


def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding='utf-8')


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


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


# ---------- AUTH ----------

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not name or not email or not password:
        return jsonify({'error': 'Заполните все поля'}), 400
    if len(password) < 4:
        return jsonify({'error': 'Пароль слишком короткий (минимум 4 символа)'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Некорректный email'}), 400
    users = load_users()
    if email in users and users[email].get('verified'):
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    users[email] = {
        'name': name,
        'email': email,
        'password': hash_password(password),
        'verified': False,
    }
    save_users(users)
    # In production we'd email this. Using fixed always-working code.
    return jsonify({'ok': True, 'message': 'Код подтверждения отправлен на email'})


@app.route('/api/auth/verify', methods=['POST'])
def verify():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()
    users = load_users()
    if email not in users:
        return jsonify({'error': 'Пользователь не найден'}), 404
    if code != VERIFICATION_CODE:
        return jsonify({'error': 'Неверный код подтверждения'}), 400
    users[email]['verified'] = True
    save_users(users)
    session['user_email'] = email
    return jsonify({'ok': True, 'user': {'name': users[email]['name'], 'email': email}})


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    users = load_users()
    user = users.get(email)
    if not user or user.get('password') != hash_password(password):
        return jsonify({'error': 'Неверный email или пароль'}), 401
    if not user.get('verified'):
        return jsonify({'error': 'Подтвердите email', 'needsVerification': True}), 403
    session['user_email'] = email
    return jsonify({'ok': True, 'user': {'name': user['name'], 'email': email}})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({'ok': True})


@app.route('/api/auth/me')
def me():
    email = session.get('user_email')
    if not email:
        return jsonify({'user': None})
    users = load_users()
    user = users.get(email)
    if not user:
        session.pop('user_email', None)
        return jsonify({'user': None})
    return jsonify({'user': {'name': user['name'], 'email': email}})


# ---------- ROUTES ----------

def require_auth():
    return bool(session.get('user_email'))


@app.route('/api/routes')
def api_routes():
    if not require_auth():
        return jsonify({'error': 'Требуется авторизация'}), 401
    return jsonify({'routes': scan_routes()})


@app.route('/api/route/<route_id>/slides')
def api_route_slides(route_id):
    if not require_auth():
        return jsonify({'error': 'Требуется авторизация'}), 401
    irf_path = ROUTES_DIR / f"{route_id}.irf"
    if not irf_path.exists():
        return jsonify({'error': 'not found'}), 404
    dest_dir = extract_irf(irf_path, route_id)
    pres = dest_dir / 'presentation.json'
    if not pres.exists():
        return jsonify({'slides': []})
    try:
        data = json.loads(pres.read_text(encoding='utf-8'))
    except Exception:
        return jsonify({'slides': []})
    slides = []
    for s in data:
        slides.append({
            'type': s.get('type', ''),
            'messages': s.get('messages', []) or [],
        })
    return jsonify({'slides': slides})


@app.route('/route/<route_id>/<path:filename>')
def serve_route_file(route_id, filename):
    if not require_auth():
        abort(401)
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
