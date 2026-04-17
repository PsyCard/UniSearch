from flask import Flask, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import os
import re
import sqlite3
import contextlib
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app, supports_credentials=True)

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False') == 'True'
if os.environ.get('SESSION_COOKIE_DOMAIN'):
    app.config['SESSION_COOKIE_DOMAIN'] = os.environ['SESSION_COOKIE_DOMAIN']

app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_CHANGE_IN_PRODUCTION')

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri='memory://',
)

# ---------------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get('DB_PATH', 'app.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


@contextlib.contextmanager
def db():
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                email     TEXT PRIMARY KEY,
                password  TEXT NOT NULL,
                name      TEXT NOT NULL DEFAULT '',
                role      TEXT NOT NULL DEFAULT 'user',
                favorites TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS universities (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                type    TEXT NOT NULL DEFAULT 'Privada',
                city    TEXT NOT NULL DEFAULT '',
                barrio  TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                phone   TEXT NOT NULL DEFAULT '',
                email   TEXT NOT NULL DEFAULT '',
                website TEXT NOT NULL DEFAULT '',
                careers TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                university_id INTEGER NOT NULL REFERENCES universities(id) ON DELETE CASCADE,
                author        TEXT NOT NULL,
                author_email  TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT '',
                rating        INTEGER NOT NULL DEFAULT 5,
                text          TEXT NOT NULL DEFAULT ''
            );
        ''')


def seed_from_json():
    """Import data.json and users.json into SQLite on first run."""
    with db() as conn:
        count = conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0]
        if count > 0:
            return  # already seeded

    if os.path.exists('data.json'):
        try:
            with open('data.json', 'r', encoding='utf-8-sig') as f:
                unis = json.load(f)
            with db() as conn:
                for u in unis:
                    conn.execute(
                        '''INSERT OR IGNORE INTO universities
                           (id, name, type, city, barrio, address, phone, email, website, careers)
                           VALUES (?,?,?,?,?,?,?,?,?,?)''',
                        (
                            u.get('id'),
                            u.get('name', ''),
                            u.get('type', 'Privada'),
                            u.get('city', ''),
                            u.get('barrio', ''),
                            u.get('address', ''),
                            u.get('phone', ''),
                            u.get('email', ''),
                            u.get('website', ''),
                            json.dumps(u.get('careers', []), ensure_ascii=False),
                        )
                    )
                    for r in u.get('reviews', []):
                        conn.execute(
                            '''INSERT INTO reviews
                               (university_id, author, author_email, role, rating, text)
                               VALUES (?,?,?,?,?,?)''',
                            (
                                u.get('id'),
                                r.get('author', ''),
                                r.get('author_email', ''),
                                r.get('role', ''),
                                int(r.get('rating', 5)),
                                r.get('text', ''),
                            )
                        )
            print(f'Seeded {len(unis)} universities from data.json')
        except Exception as e:
            print(f'Could not seed universities: {e}')

    if os.path.exists('users.json'):
        try:
            with open('users.json', 'r', encoding='utf-8-sig') as f:
                users = json.load(f)
            with db() as conn:
                for email, info in users.items():
                    conn.execute(
                        '''INSERT OR IGNORE INTO users (email, password, name, role, favorites)
                           VALUES (?,?,?,?,?)''',
                        (
                            email,
                            info.get('password', ''),
                            info.get('name', ''),
                            info.get('role', 'user'),
                            json.dumps(info.get('favorites', [])),
                        )
                    )
            print(f'Seeded {len(users)} users from users.json')
        except Exception as e:
            print(f'Could not seed users: {e}')


# Run on startup
init_db()
seed_from_json()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def is_valid_email(email):
    return bool(EMAIL_RE.match(email or ''))


def uni_to_dict(row, reviews):
    return {
        'id':      row['id'],
        'name':    row['name'],
        'type':    row['type'],
        'city':    row['city'],
        'barrio':  row['barrio'],
        'address': row['address'],
        'phone':   row['phone'],
        'email':   row['email'],
        'website': row['website'],
        'careers': json.loads(row['careers'] or '[]'),
        'reviews': reviews,
    }


def review_to_dict(row):
    return {
        'id':           row['id'],
        'author':       row['author'],
        'author_email': row['author_email'],
        'role':         row['role'],
        'rating':       row['rating'],
        'text':         row['text'],
    }


def load_reviews(conn, university_id):
    rows = conn.execute(
        'SELECT * FROM reviews WHERE university_id=? ORDER BY id DESC', (university_id,)
    ).fetchall()
    return [review_to_dict(r) for r in rows]


def require_admin(email):
    if not email:
        return False
    with db() as conn:
        row = conn.execute('SELECT role FROM users WHERE email=?', (email,)).fetchone()
    return bool(row and row['role'] == 'admin')


# ---------------------------------------------------------------------------
# Static pages (admin/dashboard protected server-side)
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/dashboard.html')
def dashboard():
    email = session.get('email')
    if not email or not require_admin(email):
        return redirect(url_for('index'))
    return app.send_static_file('dashboard.html')


@app.route('/admin.html')
def admin():
    email = session.get('email')
    if not email or not require_admin(email):
        return redirect(url_for('index'))
    return app.send_static_file('admin.html')


# ---------------------------------------------------------------------------
# API — universities
# ---------------------------------------------------------------------------
@app.route('/api/universities', methods=['GET'])
def get_universities():
    with db() as conn:
        rows = conn.execute('SELECT * FROM universities ORDER BY id').fetchall()
        result = [uni_to_dict(row, load_reviews(conn, row['id'])) for row in rows]
    return jsonify(result)


@app.route('/api/universities', methods=['POST'])
def add_university():
    email = session.get('email')
    if not require_admin(email):
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    data = request.get_json() or {}
    careers_raw = data.get('careers', [])
    careers = careers_raw if isinstance(careers_raw, list) else [
        c.strip() for c in str(careers_raw).split(',') if c.strip()
    ]
    with db() as conn:
        cur = conn.execute(
            '''INSERT INTO universities (name, type, city, barrio, address, phone, email, website, careers)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (
                data.get('name', 'Sin nombre'),
                data.get('type', 'Privada'),
                data.get('city', ''),
                data.get('barrio', ''),
                data.get('address', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('website', ''),
                json.dumps(careers, ensure_ascii=False),
            )
        )
        row = conn.execute('SELECT * FROM universities WHERE id=?', (cur.lastrowid,)).fetchone()
        result = uni_to_dict(row, [])
    return jsonify({'success': True, 'university': result}), 201


@app.route('/api/universities/<int:uid>', methods=['PUT'])
def update_university(uid):
    email = session.get('email')
    if not require_admin(email):
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    data = request.get_json() or {}
    with db() as conn:
        row = conn.execute('SELECT * FROM universities WHERE id=?', (uid,)).fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'No encontrada'}), 404
        careers = data.get('careers', json.loads(row['careers'] or '[]'))
        if isinstance(careers, str):
            careers = [c.strip() for c in careers.split(',') if c.strip()]
        conn.execute(
            '''UPDATE universities
               SET name=?,type=?,city=?,barrio=?,address=?,phone=?,email=?,website=?,careers=?
               WHERE id=?''',
            (
                data.get('name',    row['name']),
                data.get('type',    row['type']),
                data.get('city',    row['city']),
                data.get('barrio',  row['barrio']),
                data.get('address', row['address']),
                data.get('phone',   row['phone']),
                data.get('email',   row['email']),
                data.get('website', row['website']),
                json.dumps(careers, ensure_ascii=False),
                uid,
            )
        )
        updated = conn.execute('SELECT * FROM universities WHERE id=?', (uid,)).fetchone()
        result = uni_to_dict(updated, load_reviews(conn, uid))
    return jsonify({'success': True, 'university': result})


@app.route('/api/universities/<int:uid>', methods=['DELETE'])
def delete_university(uid):
    email = session.get('email')
    if not require_admin(email):
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    with db() as conn:
        affected = conn.execute('DELETE FROM universities WHERE id=?', (uid,)).rowcount
    if not affected:
        return jsonify({'success': False, 'message': 'No encontrada'}), 404
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — reviews
# ---------------------------------------------------------------------------
@app.route('/api/universities/<int:uid>/reviews', methods=['GET'])
def get_reviews(uid):
    with db() as conn:
        uni = conn.execute('SELECT id FROM universities WHERE id=?', (uid,)).fetchone()
        if not uni:
            return jsonify([]), 404
        return jsonify(load_reviews(conn, uid))


@app.route('/api/universities/<int:uid>/reviews', methods=['POST'])
def add_review(uid):
    author_email = session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para dejar reseña'}), 401
    data   = request.get_json() or {}
    rating = data.get('rating')
    text   = str(data.get('text', '')).strip()
    if rating is None or not text:
        return jsonify({'success': False, 'message': 'Rating y texto son requeridos'}), 400
    with db() as conn:
        if not conn.execute('SELECT id FROM universities WHERE id=?', (uid,)).fetchone():
            return jsonify({'success': False, 'message': 'Universidad no encontrada'}), 404
        if conn.execute(
            'SELECT id FROM reviews WHERE university_id=? AND author_email=?', (uid, author_email)
        ).fetchone():
            return jsonify({'success': False, 'message': 'Ya existe una reseña de esta cuenta'}), 409
        user_row = conn.execute('SELECT name FROM users WHERE email=?', (author_email,)).fetchone()
        author = (user_row['name'] if user_row else '') or author_email
        cur = conn.execute(
            'INSERT INTO reviews (university_id, author, author_email, role, rating, text) VALUES (?,?,?,?,?,?)',
            (uid, author, author_email, data.get('role', ''), int(rating), text)
        )
        row = conn.execute('SELECT * FROM reviews WHERE id=?', (cur.lastrowid,)).fetchone()
    return jsonify({'success': True, 'review': review_to_dict(row)}), 201


@app.route('/api/universities/<int:uid>/reviews', methods=['PUT'])
def update_review(uid):
    author_email = session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401
    data   = request.get_json() or {}
    rating = data.get('rating')
    text   = str(data.get('text', '')).strip()
    if rating is None or not text:
        return jsonify({'success': False, 'message': 'Rating y texto son requeridos'}), 400
    with db() as conn:
        row = conn.execute(
            'SELECT * FROM reviews WHERE university_id=? AND author_email=?', (uid, author_email)
        ).fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Reseña no encontrada'}), 404
        conn.execute(
            'UPDATE reviews SET role=?, rating=?, text=? WHERE id=?',
            (data.get('role', row['role']), int(rating), text, row['id'])
        )
        updated = conn.execute('SELECT * FROM reviews WHERE id=?', (row['id'],)).fetchone()
    return jsonify({'success': True, 'review': review_to_dict(updated)})


@app.route('/api/universities/<int:uid>/reviews', methods=['DELETE'])
def delete_review(uid):
    author_email = session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión'}), 401
    with db() as conn:
        affected = conn.execute(
            'DELETE FROM reviews WHERE university_id=? AND author_email=?', (uid, author_email)
        ).rowcount
    if not affected:
        return jsonify({'success': False, 'message': 'Reseña no encontrada'}), 404
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# API — auth (rate-limited)
# ---------------------------------------------------------------------------
@app.route('/api/signup', methods=['POST'])
@limiter.limit('10 per hour')
def signup():
    data     = request.get_json() or {}
    email    = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    name     = str(data.get('name', '')).strip()

    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'Email, contraseña y nombre son requeridos'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400

    with db() as conn:
        if conn.execute('SELECT email FROM users WHERE email=?', (email,)).fetchone():
            return jsonify({'success': False, 'message': 'El email ya está registrado'}), 409
        conn.execute(
            'INSERT INTO users (email, password, name, role, favorites) VALUES (?,?,?,?,?)',
            (email, generate_password_hash(password), name, 'user', '[]')
        )
    session['email'] = email
    return jsonify({'success': True, 'message': 'Registro exitoso'})


@app.route('/api/login', methods=['POST'])
@limiter.limit('20 per hour; 5 per minute')
def login():
    data     = request.get_json() or {}
    email    = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contraseña son requeridos'}), 400
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400

    with db() as conn:
        row = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()

    if not row or not check_password_hash(row['password'], password):
        return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

    session['email'] = email
    return jsonify({'success': True, 'message': 'Login exitoso'})


@app.route('/api/logout')
def logout():
    session.clear()
    resp = jsonify({'success': True, 'message': 'Sesión cerrada'})
    resp.set_cookie('session', '', max_age=0, path='/')
    return resp


@app.route('/api/user')
def get_user():
    email = session.get('email')
    if not email:
        return jsonify({'logged_in': False})
    with db() as conn:
        row = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    if not row:
        session.clear()
        return jsonify({'logged_in': False})
    return jsonify({
        'logged_in': True,
        'email':     row['email'],
        'name':      row['name'],
        'role':      row['role'],
        'favorites': json.loads(row['favorites'] or '[]'),
    })


@app.route('/api/ping')
def api_ping():
    return jsonify({'ok': True, 'app': os.path.basename(__file__)})


# ---------------------------------------------------------------------------
# Rate-limit error handler
# ---------------------------------------------------------------------------
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'message': 'Demasiados intentos. Espera un momento.'}), 429


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
