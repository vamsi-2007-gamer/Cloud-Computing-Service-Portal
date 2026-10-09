import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "cloud_portal.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "csv", "xlsx", "ppt", "pptx", "png", "jpg", "jpeg", "gif", "zip"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        original_name TEXT NOT NULL,
        stored_name TEXT NOT NULL,
        size INTEGER NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} GB"

@app.context_processor
def inject_helpers():
    return {"format_size": format_size}

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, generate_password_hash(password))
                )
                conn.commit()
                flash("Account created. You can now sign in.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("An account with that email already exists.", "error")
            finally:
                conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    user_files = conn.execute(
        "SELECT * FROM files WHERE user_id = ? ORDER BY uploaded_at DESC",
        (session["user_id"],)
    ).fetchall()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    total = sum(f["size"] for f in user_files)
    return render_template("dashboard.html", files=user_files, user=user, total_size=total)

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if "file" not in request.files:
        flash("No file selected.", "error")
        return redirect(url_for("dashboard"))

    file = request.files["file"]
    if not file.filename:
        flash("No file selected.", "error")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("This file type is not supported.", "error")
        return redirect(url_for("dashboard"))

    original = secure_filename(file.filename)
    stored = f"{session['user_id']}_{os.urandom(10).hex()}_{original}"
    path = os.path.join(UPLOAD_FOLDER, stored)
    file.save(path)
    size = os.path.getsize(path)

    conn = get_db()
    conn.execute(
        "INSERT INTO files (user_id, original_name, stored_name, size) VALUES (?, ?, ?, ?)",
        (session["user_id"], original, stored, size)
    )
    conn.commit()
    conn.close()
    flash(f"{original} uploaded successfully.", "success")
    return redirect(url_for("dashboard"))

@app.route("/download/<int:file_id>")
@login_required
def download(file_id):
    conn = get_db()
    record = conn.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"])
    ).fetchone()
    conn.close()
    if not record:
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))
    return send_from_directory(UPLOAD_FOLDER, record["stored_name"], as_attachment=True, download_name=record["original_name"])

@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id):
    conn = get_db()
    record = conn.execute(
        "SELECT * FROM files WHERE id = ? AND user_id = ?",
        (file_id, session["user_id"])
    ).fetchone()
    if not record:
        conn.close()
        flash("File not found.", "error")
        return redirect(url_for("dashboard"))

    path = os.path.join(UPLOAD_FOLDER, record["stored_name"])
    if os.path.exists(path):
        os.remove(path)
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()
    flash(f"{record['original_name']} deleted.", "success")
    return redirect(url_for("dashboard"))

@app.route("/api/stats")
@login_required
def stats():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM files WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
    total = conn.execute("SELECT COALESCE(SUM(size), 0) FROM files WHERE user_id = ?", (session["user_id"],)).fetchone()[0]
    conn.close()
    return jsonify({"files": count, "bytes": total, "formatted": format_size(total)})

@app.errorhandler(413)
def too_large(_):
    flash("File is too large. Maximum upload size is 50 MB.", "error")
    return redirect(url_for("dashboard"))

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
