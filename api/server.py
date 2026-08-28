"""
CSC 6304 — Week 5: Full Stack Flask API with SQLite Persistence

This is your Flask API from Weeks 3-4, now with database persistence and JWT auth.
Gunicorn serves this app in production (see Containerfile).

Your job: implement the database logic and JWT authentication in the route handlers.
Flask handles HTTP parsing, routing, and JSON serialization.
SQLite handles data storage.
"""

import os
import requests
import datetime
import sqlite3
import jwt
from dotenv import load_dotenv
from flask import Flask, request, jsonify, g, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables from .env (if present).
# In containers, compose.yml's env_file directive already sets these,
# so load_dotenv() is a no-op — it won't override existing env vars.
load_dotenv()

HARNESS_URL = os.environ.get('HARNESS_URL', 'http://harness:9090')

app = Flask(__name__)

# Read configuration from environment variables.
# Defaults are used if the variable isn't set (e.g., .env is missing).
DB_PATH = os.getenv('DB_PATH', 'data/chat.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
CHAT_PASSWORD = os.getenv('CHAT_PASSWORD', 'change-me')

# CORS: In development, the Vite dev server runs on localhost:5173 and the
# Flask API runs on localhost:8080 — different origins, so the browser
# requires CORS headers. In production, Flask serves both the frontend and
# the API on the same origin (Sprites.dev), so CORS is not triggered.
#
# TODO: Add the Vite dev server origin so the browser allows cross-origin
# requests during development.
# Hint: The Vite dev server runs at http://localhost:5173
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:8081"
    "http://localhost:8080"
], supports_credentials=True)



# ---------------------------------------------------------------------------
# JWT Authentication
# ---------------------------------------------------------------------------
# The flow:
#   1. User enters the chat password in a form on the frontend.
#   2. Frontend POSTs to /auth with { "password": "<password>" }.
#   3. Server looks up the password hash from the SQLite database and
#      verifies it with check_password_hash().
#   4. If valid, server signs a JWT with SECRET_KEY, returns { "token": "..." },
#      and sets an httpOnly cookie.
#   5. Frontend stores the token in memory (for the Bearer header approach).
#   6. On protected routes (/chat, /history), the browser sends the cookie
#      automatically. Alternatively the frontend can send Authorization: Bearer <token>.
#   7. The @app.before_request middleware below verifies the JWT on every
#      protected request.
#
# Two separate secrets:
#   - CHAT_PASSWORD: the user-facing password (hashed and stored in the DB)
#   - SECRET_KEY:    the JWT signing key (lives only in app.config, never sent to client)


@app.route('/auth', methods=['POST'])
def auth():
    """
    POST /auth
    Request:  { "password": "<chat-password>" }
    Response: { "token": "<JWT>" }   (status 200)
    Also sets an httpOnly cookie named "auth_token".
    Returns 401 if the password doesn't match the stored hash.
    """
    body = request.get_json(silent=True) or {}
    provided_password = body.get('password', '')

    # TODO: Look up the stored password hash from the database and verify
    #       the provided password against it.
    #       Return 401 if they don't match.
    #       Hint:
    #         db = get_db()
    #         row = db.execute('SELECT password_hash FROM auth WHERE id = 1').fetchone()
    #         if not row or not check_password_hash(row['password_hash'], provided_password):
    #             return jsonify({"error": "Invalid password"}), 401
    db = get_db()
    row = db.execute('SELECT password_hash FROM auth WHERE id = 1').fetchone()
    if not row or not check_password_hash(row['password_hash'], provided_password):
        return jsonify({"error": "Invalid password"}), 401

    # TODO: Build a JWT payload with "sub", "iat", and "exp" (1 hour from now).
    #       Sign it with app.config['SECRET_KEY'] using HS256.
    #       Hint:
    #         now = datetime.datetime.now(datetime.timezone.utc)
    #         payload = {
    #             "sub": "chat-user",
    #             "iat": now,
    #             "exp": now + datetime.timedelta(hours=1),
    #         }
    #         token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": "chat-user",
        "iat": now,
        "exp": now + datetime.timedelta(hours=1),
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    # TODO: Return the token in JSON AND as an httpOnly cookie.
    #       Use make_response() and set_cookie() as shown below.
    #
    #       response = make_response(jsonify({"token": token}), 200)
    #       response.set_cookie(
    #           "auth_token",
    #           token,
    #           httponly=True,    # JavaScript cannot read this cookie
    #           secure=True,      # HTTPS only (Sprites.dev). In local dev over HTTP,
    #                             # the cookie won't be set — use the Bearer header instead.
    #           samesite="None",  # allows cross-origin in dev; harmless in prod (same origin)
    #           max_age=3600,     # 1 hour — matches JWT expiry
    #       )
    #       return response
    response = make_response(jsonify({"token": token}), 200)
    response.set_cookie(
        "auth_token",
        token,
        httponly=True,
        secure=True,
        samesite="None",
        max_age=3600,
    )
    return response


@app.before_request
def verify_jwt():
    """
    Middleware that runs before every request.
    Verifies the JWT on protected routes (/chat, /history).
    Allows /auth, /, and OPTIONS (CORS preflight) without a token.
    """
    # Allow auth, index, and CORS preflight without a token
    if request.path in ('/auth', '/') or request.path.startswith('/assets/') or request.method == 'OPTIONS':
        return

    # TODO: Extract the token from the Authorization header or the auth_token cookie.
    #       Check "Authorization: Bearer <token>" first, then fall back to the cookie.
    #       Return 401 if no token is found.
    #       Hint:
    #         auth_header = request.headers.get("Authorization", "")
    #         if auth_header.startswith("Bearer "):
    #             token = auth_header[len("Bearer "):]
    #         else:
    #             token = request.cookies.get("auth_token")
    #             if not token:
    #                 return jsonify({"error": "Missing token"}), 401
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
    else:
        token = request.cookies.get("auth_token")
        if not token:
            return jsonify({"error": "Missing token"}), 401

    # TODO: Verify the JWT using jwt.decode().
    #       Catch jwt.ExpiredSignatureError and jwt.InvalidTokenError.
    #       Return 401 for each case.
    #       Hint:
    #         try:
    #             jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    #         except jwt.ExpiredSignatureError:
    #             return jsonify({"error": "Token expired"}), 401
    #         except jwt.InvalidTokenError:
    #             return jsonify({"error": "Invalid token"}), 401
    try:
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # If we get here, the token is valid — continue to the route handler.


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """
    Get a database connection for the current request.
    Flask's `g` object stores per-request data.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        # This lets us access columns by name: row['message']
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create the messages and auth tables if they don't exist.
    Also stores the hashed CHAT_PASSWORD in the auth table.
    """
    db = sqlite3.connect(DB_PATH)

    # Messages table — stores every chat message and its response.
    db.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Auth table — stores the hashed chat password.
    # The CHECK(id = 1) constraint ensures only one row (universal password).
    db.execute('''
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            password_hash TEXT NOT NULL
        )
    ''')

    # Store or update the password hash.
    # This runs on every startup, so changing CHAT_PASSWORD in .env
    # and restarting the server updates the stored hash.
    password_hash = generate_password_hash(CHAT_PASSWORD)
    db.execute('''
        INSERT INTO auth (id, password_hash) VALUES (1, ?)
        ON CONFLICT(id) DO UPDATE SET password_hash = excluded.password_hash
    ''', (password_hash,))

    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/chat', methods=['POST'])
def chat():
    """
    POST /chat
    Request:  { "message": "hello" }
    Response: { "response": "hello" }   (status 201 Created)

    TODO:
    1. Parse the JSON body (use request.get_json())
       - Return 400 if the body isn't valid JSON or 'message' is missing
    2. Create the response (echo the message for now)
    3. INSERT the message and response into the messages table
    4. Return { "response": response } with status 201

    Hint: Use get_db() to get the connection, then db.execute() and db.commit()
    """
    body = request.get_json(silent=True)
    if not body or 'message' not in body or not body['message']:
        return jsonify({'error': 'Missing message'}), 400

    message = body['message']

    try:
        resp = requests.post(
            f'{HARNESS_URL}/chat', json={'message': message}, timeout=300,
        )
        response_text = resp.json()['response']
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Agent harness unavailable: {e}'}), 502
    except (KeyError, ValueError) as e:
        return jsonify({'error': f'Bad response from harness: {e}'}), 502

    db = get_db()
    db.execute('INSERT INTO messages (message, response) VALUES (?,?)', (message, response_text))
    db.commit()

    return jsonify({'response': response_text}), 201


@app.route('/history', methods=['GET'])
def get_history():
    """
    GET /history
    Response: [ { "message": "...", "response": "...", "created_at": "..." }, ... ]
    (status 200 OK)

    TODO:
    1. SELECT all messages from the database, ordered by created_at
    2. Convert each row to a dict: dict(row)
    3. Return the list with jsonify()

    Hint:
        db = get_db()
        rows = db.execute('SELECT ... ORDER BY ...').fetchall()
        return jsonify([dict(row) for row in rows])
    """
    db = get_db()
    rows = db.execute('SELECT message, response, created_at FROM messages ORDER BY created_at').fetchall()
    return jsonify([dict(row) for row in rows]), 200


@app.route('/')
def index():
    """Serve the chat UI (in production, nginx handles this instead)."""
    from flask import send_from_directory
    return send_from_directory('../static', 'index.html')

@app.route('/assets/<path:filename>') # I needed to run this in order to avoid 404 errors from happening.
def serve_assets(filename):
    from flask import send_from_directory
    return send_from_directory('../static/assets', filename)


# Initialize the database when the app starts
init_db()

if __name__ == '__main__': 
    # Development mode — gunicorn is used in production (see Containerfile)
    host = os.getenv('HOST', '::')
    port = int(os.getenv('PORT', '8080'))
    app.run(host=host, port=port, debug=True)
