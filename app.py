
import os
import hmac
import sqlite3
from pathlib import Path
from functools import wraps

from flask import (
    Flask, request, jsonify, send_from_directory,
    redirect, url_for, session, render_template_string
)

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "bookings.db"

# Password aur secret environment variables se aayenge
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not ADMIN_PASSWORD or not SECRET_KEY:
    raise RuntimeError(
        "Set ADMIN_PASSWORD and SECRET_KEY before starting the server."
    )

app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)


def create_database():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                car_brand TEXT NOT NULL,
                car_model TEXT NOT NULL,
                service TEXT NOT NULL,
                date TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


create_database()


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def home():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/<path:filename>")
def website_files(filename):
    if filename in ("style.css", "script.js"):
        return send_from_directory(str(BASE_DIR), filename)
    return "File not found", 404


@app.route("/api/bookings", methods=["POST"])
def save_booking():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid booking data"}), 400

    required_fields = [
        "customer_name", "phone", "car_brand", "car_model", "service"
    ]

    for field in required_fields:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            return jsonify({"error": f"{field} is required"}), 400

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.execute("""
            INSERT INTO bookings (
                customer_name, phone, car_brand, car_model,
                service, date, details
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["customer_name"].strip(),
            data["phone"].strip(),
            data["car_brand"].strip(),
            data["car_model"].strip(),
            data["service"].strip(),
            str(data.get("date", "")),
            str(data.get("details", ""))
        ))
        booking_id = cursor.lastrowid

    return jsonify({
        "message": "Booking saved successfully!",
        "booking_id": booking_id
    }), 201


LOGIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin Login | Boost Boyz</title>
<style>
body{font-family:Arial,sans-serif;background:#111;color:#fff;
display:grid;place-items:center;min-height:100vh;margin:0}
form{background:#222;padding:28px;border-radius:12px;width:min(320px,80vw)}
input,button{box-sizing:border-box;width:100%;padding:12px;margin-top:12px}
button{background:#f5b400;border:0;font-weight:bold;cursor:pointer}
.error{color:#ff9c9c}
</style>
</head>
<body>
<form method="post">
<h2>Boost Boyz Admin</h2>
<p>Login to view bookings.</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<input type="password" name="password" placeholder="Admin password"
required autocomplete="current-password">
<button type="submit">Login</button>
</form>
</body>
</html>
"""


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin"))

    error = None

    if request.method == "POST":
        supplied = request.form.get("password", "")
        if hmac.compare_digest(supplied, ADMIN_PASSWORD):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin"))
        error = "Incorrect password. Try again."

    return render_template_string(LOGIN_PAGE, error=error)


@app.route("/admin")
@admin_required
def admin():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        bookings = conn.execute("""
            SELECT id, customer_name, phone, car_brand, car_model,
                   service, date, details, created_at
            FROM bookings
            ORDER BY id DESC
        """).fetchall()

    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Bookings | Boost Boyz</title>
    <style>
    body{font-family:Arial,sans-serif;background:#f3f3f3;color:#222;
    margin:0;padding:20px}
    header{display:flex;justify-content:space-between;align-items:center;
    gap:12px;flex-wrap:wrap}
    a.button{background:#222;color:#fff;padding:10px 14px;
    text-decoration:none;border-radius:6px}
    .booking{background:white;padding:16px;margin:14px 0;
    border-radius:10px;overflow-wrap:anywhere}
    .muted{color:#666;font-size:14px}
    </style>
    </head>
    <body>
    <header>
      <div><h1>Boost Boyz Bookings</h1>
      <p>Total bookings: {{ bookings|length }}</p></div>
      <a class="button" href="{{ url_for('admin_logout') }}">Logout</a>
    </header>
    {% for b in bookings %}
    <article class="booking">
      <h3>#{{ b['id'] }} — {{ b['customer_name'] }}</h3>
      <p><b>Phone:</b> {{ b['phone'] }}</p>
      <p><b>Car:</b> {{ b['car_brand'] }} {{ b['car_model'] }}</p>
      <p><b>Service:</b> {{ b['service'] }}</p>
      <p><b>Requested date:</b> {{ b['date'] or 'Not provided' }}</p>
      <p><b>Details:</b> {{ b['details'] or 'None' }}</p>
      <p class="muted">Booking received: {{ b['created_at'] }}</p>
    </article>
    {% else %}
    <p>No bookings found yet.</p>
    {% endfor %}
    </body>
    </html>
    """, bookings=bookings)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    print("Boost Boyz Automotive server starting...")
    print(f"Database location: {DATABASE}")
    app.run(debug=True)
