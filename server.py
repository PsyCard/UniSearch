from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for
from flask_cors import CORS
import json
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash

# use Flask's built-in static serving so we don't accidentally intercept
# API paths; set static_folder to the current directory and serve at root
app = Flask(__name__, static_folder='.', static_url_path='')
# allow credentials for cross‑origin if deployed behind a CDN or different domain
CORS(app, supports_credentials=True)
# session configuration from environment for production
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE','False') == 'True'
# By default Flask sets domain to current host; override via env if needed
if os.environ.get('SESSION_COOKIE_DOMAIN'):
    app.config['SESSION_COOKIE_DOMAIN'] = os.environ['SESSION_COOKIE_DOMAIN']

# secret key should come from environment in production
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')  # override externally

# Archivo para almacenar usuarios
USERS_FILE = 'users.json'

# Crear archivo de usuarios si no existe
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def is_valid_email(email):
    """Validar formato básico de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Crear data.json si no existe
if not os.path.exists('data.json'):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump([], f)


# load data from file on demand

def load_universities():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

universities = load_universities()

@app.route('/')
def index():
    # send the main landing page
    return app.send_static_file('index.html')

@app.route('/dashboard.html')
def dashboard():
    # protect dashboard: require login and specific emails
    allowed_emails = ['jgmejia@unibarranquilla.edu.co', 'erjaimes@unibarranquilla.edu.co']
    if 'email' not in session or session['email'] not in allowed_emails:
        return redirect(url_for('index'))
    return app.send_static_file('dashboard.html')

@app.route('/admin.html')
def admin():
    # protect admin dashboard: require login and specific emails
    allowed_emails = ['jgmejia@unibarranquilla.edu.co', 'erjaimes@unibarranquilla.edu.co']
    if 'email' not in session or session['email'] not in allowed_emails:
        return redirect(url_for('index'))
    return app.send_static_file('admin.html')

# we no longer need a catch‑all route for static files; Flask will serve
# anything under the static_folder automatically (app.static_folder).
# Keeping a generic "<path:path>" route above the API endpoints was
# causing API requests such as `/api/universities` to be treated as
# file requests and return 404 instead of hitting the appropriate view.

@app.route('/api/universities')
def get_universities():
    # always read latest data
    unis = load_universities()
    return jsonify(unis)

# reviews endpoints
@app.route('/api/universities/<int:uid>/reviews')
def get_reviews(uid):
    unis = load_universities()
    uni = next((u for u in unis if u.get('id') == uid), None)
    if not uni:
        return jsonify([]), 404
    return jsonify(uni.get('reviews', []))

@app.route('/api/universities', methods=['POST'])
def add_university():
    data = request.get_json() or {}
    unis = load_universities()
    new_id = max([u.get('id', 0) for u in unis], default=0) + 1
    new_uni = {
        'id': new_id,
        'name': data.get('name', 'Sin nombre'),
        'type': data.get('type', 'Privada'),
        'city': data.get('city', ''),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'website': data.get('website', ''),
        'careers': data.get('careers', []),
        'reviews': []
    }
    unis.append(new_uni)
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'university': new_uni}), 201

@app.route('/api/universities/<int:uid>', methods=['PUT'])
def update_university(uid):
    data = request.get_json() or {}
    unis = load_universities()
    uni = next((u for u in unis if u.get('id') == uid), None)
    if not uni:
        return jsonify({'success': False, 'message': 'University not found'}), 404

    uni['name'] = data.get('name', uni.get('name', 'Sin nombre'))
    uni['type'] = data.get('type', uni.get('type', 'Privada'))
    uni['city'] = data.get('city', uni.get('city', ''))
    uni['phone'] = data.get('phone', uni.get('phone', ''))
    uni['email'] = data.get('email', uni.get('email', ''))
    uni['website'] = data.get('website', uni.get('website', ''))
    uni['careers'] = data.get('careers', uni.get('careers', []))

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'university': uni})

@app.route('/api/universities/<int:uid>', methods=['DELETE'])
def delete_university(uid):
    unis = load_universities()
    original_len = len(unis)
    unis = [u for u in unis if u.get('id') != uid]
    if len(unis) == original_len:
        return jsonify({'success': False, 'message': 'University not found'}), 404
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'message': 'University deleted'})


# review submission endpoint was accidentally placed inside the delete
# handler earlier; extract it here so the client can POST reviews as
# intended.
@app.route('/api/universities/<int:uid>/reviews', methods=['POST'])
def add_review(uid):
    data = request.get_json() or {}
    author_email = data.get('author_email') or session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para dejar reseña'}), 400

    author = data.get('author') or author_email
    role = data.get('role', '')
    rating = data.get('rating')
    text = data.get('text')
    if rating is None or text is None:
        return jsonify({'success': False, 'message': 'Rating and text required'}), 400

    unis = load_universities()
    uni = next((u for u in unis if u.get('id') == uid), None)
    if not uni:
        return jsonify({'success': False, 'message': 'University not found'}), 404

    reviews = uni.setdefault('reviews', [])
    if any(r.get('author_email') == author_email for r in reviews):
        return jsonify({'success': False, 'message': 'Ya existe una reseña de esta cuenta'}), 409

    new_id = max([r.get('id', 0) for r in reviews], default=0) + 1
    review = {
        'id': new_id,
        'author': author,
        'author_email': author_email,
        'role': role,
        'rating': rating,
        'text': text
    }
    reviews.append(review)

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'review': review})

@app.route('/api/universities/<int:uid>/reviews', methods=['PUT'])
def update_review(uid):
    data = request.get_json() or {}
    author_email = data.get('author_email') or session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para editar reseña'}), 400

    role = data.get('role', '')
    rating = data.get('rating')
    text = data.get('text')
    if rating is None or text is None:
        return jsonify({'success': False, 'message': 'Rating and text required'}), 400

    unis = load_universities()
    uni = next((u for u in unis if u.get('id') == uid), None)
    if not uni:
        return jsonify({'success': False, 'message': 'University not found'}), 404

    reviews = uni.get('reviews', [])
    review = next((r for r in reviews if r.get('author_email') == author_email), None)
    if not review:
        return jsonify({'success': False, 'message': 'Review not found'}), 404

    review['author'] = data.get('author', review.get('author', author_email))
    review['role'] = role
    review['rating'] = rating
    review['text'] = text

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True, 'review': review})

@app.route('/api/universities/<int:uid>/reviews', methods=['DELETE'])
def delete_review(uid):
    data = request.get_json() or {}
    author_email = data.get('author_email') or session.get('email')
    if not author_email:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para eliminar reseña'}), 400

    unis = load_universities()
    uni = next((u for u in unis if u.get('id') == uid), None)
    if not uni:
        return jsonify({'success': False, 'message': 'University not found'}), 404

    reviews = uni.get('reviews', [])
    filtered = [r for r in reviews if r.get('author_email') != author_email]
    if len(filtered) == len(reviews):
        return jsonify({'success': False, 'message': 'Review not found'}), 404

    uni['reviews'] = filtered
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(unis, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')

    if not email or not password or not name:
        return jsonify({'success': False, 'message': 'Email, contraseña y nombre son requeridos'}), 400

    # Validar formato de email
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400

    users = load_users()
    if email in users:
        return jsonify({'success': False, 'message': 'El email ya está registrado'}), 400

    users[email] = {
        'password': generate_password_hash(password),
        'name': name,
        'favorites': []
    }
    save_users(users)

    session['email'] = email
    return jsonify({'success': True, 'message': 'Registro exitoso'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contraseña son requeridos'}), 400

    # Validar formato de email
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Formato de email inválido'}), 400

    users = load_users()
    if email in users and check_password_hash(users[email]['password'], password):
        session['email'] = email
        # Flask will send a Set-Cookie header automatically; log for debugging
        print('user logged in, session cookie will be sent')
        return jsonify({'success': True, 'message': 'Login exitoso'})
    print('login failed for', email)
    return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

@app.route('/api/logout')
def logout():
    session.clear()
    resp = jsonify({'success': True, 'message': 'Sesión cerrada'})
    # Force browser to clear the session cookie by setting max-age=0
    resp.set_cookie('session', '', max_age=0, path='/')
    return resp

@app.route('/api/user')
def get_user():
    if 'email' in session:
        users = load_users()
        user_data = users.get(session['email'], {})
        return jsonify({
            'logged_in': True,
            'email': session['email'],
            'name': user_data.get('name', ''),
            'role': user_data.get('role', 'user'),
            'favorites': user_data.get('favorites', [])
        })
    return jsonify({'logged_in': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)



