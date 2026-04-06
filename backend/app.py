import os
from functools import wraps
from datetime import datetime

import pymysql
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from pymysql.cursors import DictCursor
from werkzeug.security import check_password_hash, generate_password_hash


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")
app.config["JSON_SORT_KEYS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
CORS(
    app,
    supports_credentials=True,
    resources={r"/api/*": {"origins": [frontend_origin]}},
)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
ALLOWED_JOB_STATUSES = {"in_progress", "interview", "offer", "rejected"}


def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=True,
    )


def current_user_payload():
    return {
        "id": session["user_id"],
        "username": session["username"],
    }


def validate_birth_date(raw_value):
    if not raw_value:
        return None

    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return None


def normalize_job_status(raw_value):
    status = (raw_value or "in_progress").strip().lower()
    return status if status in ALLOWED_JOB_STATUSES else None


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401
        return view_func(*args, **kwargs)

    return wrapped_view


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@app.get("/api/session")
def get_session():
    if "user_id" not in session:
        return jsonify({"authenticated": False, "user": None})

    return jsonify({"authenticated": True, "user": current_user_payload()})


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    birth_date = validate_birth_date(data.get("birth_date", "").strip())

    if not username or not password or not birth_date:
        return jsonify({"error": "Username, password, and birth date are required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return jsonify({"error": "Username already exists."}), 409

            cursor.execute(
                """
                INSERT INTO users (username, password_hash, birth_date)
                VALUES (%s, %s, %s)
                """,
                (username, generate_password_hash(password), birth_date),
            )

        return jsonify({"message": "Registration successful."}), 201
    finally:
        conn.close()


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid username or password."}), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return jsonify(
            {"message": "Logged in successfully.", "user": current_user_payload()}
        )
    finally:
        conn.close()


@app.post("/api/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    birth_date = validate_birth_date(data.get("birth_date", "").strip())
    new_password = data.get("new_password", "")

    if not username or not birth_date or not new_password:
        return jsonify(
            {"error": "Username, birth date, and new password are required."}
        ), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username = %s AND birth_date = %s
                """,
                (username, birth_date),
            )
            user = cursor.fetchone()

            if not user:
                return jsonify({"error": "Recovery details do not match."}), 404

            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (generate_password_hash(new_password), user["id"]),
            )

        return jsonify({"message": "Password reset successfully."})
    finally:
        conn.close()


@app.post("/api/logout")
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})


@app.get("/api/jobs")
@login_required
def list_jobs():
    keyword = request.args.get("q", "").strip()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if keyword:
                search_value = f"%{keyword}%"
                cursor.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE user_id = %s
                      AND (
                          company LIKE %s OR
                          title LIKE %s OR
                          status LIKE %s OR
                          website LIKE %s OR
                          job_link LIKE %s OR
                          description LIKE %s
                      )
                    ORDER BY id DESC
                    """,
                    (
                        session["user_id"],
                        search_value,
                        search_value,
                        search_value,
                        search_value,
                        search_value,
                        search_value,
                    ),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM jobs
                    WHERE user_id = %s
                    ORDER BY id DESC
                    """,
                    (session["user_id"],),
                )

            jobs = cursor.fetchall()

        return jsonify({"jobs": jobs})
    finally:
        conn.close()


@app.post("/api/jobs")
@login_required
def create_job():
    data = request.get_json(silent=True) or {}
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    website = data.get("website", "").strip()
    job_link = data.get("job_link", "").strip()
    description = data.get("description", "").strip()
    status = normalize_job_status(data.get("status"))

    if not company or not title:
        return jsonify({"error": "Company and job title are required."}), 400

    if not status:
        return jsonify({"error": "A valid job status is required."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO jobs (user_id, company, title, website, job_link, description, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    company,
                    title,
                    website,
                    job_link,
                    description,
                    status,
                ),
            )
            job_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE id = %s AND user_id = %s
                """,
                (job_id, session["user_id"]),
            )
            job = cursor.fetchone()

        return jsonify({"message": "Job saved successfully.", "job": job}), 201
    finally:
        conn.close()


@app.get("/api/jobs/<int:job_id>")
@login_required
def get_job(job_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE id = %s AND user_id = %s
                """,
                (job_id, session["user_id"]),
            )
            job = cursor.fetchone()

        if not job:
            return jsonify({"error": "Job not found."}), 404

        return jsonify({"job": job})
    finally:
        conn.close()


@app.put("/api/jobs/<int:job_id>")
@login_required
def update_job(job_id):
    data = request.get_json(silent=True) or {}
    company = data.get("company", "").strip()
    title = data.get("title", "").strip()
    website = data.get("website", "").strip()
    job_link = data.get("job_link", "").strip()
    description = data.get("description", "").strip()
    status = normalize_job_status(data.get("status"))

    if not company or not title:
        return jsonify({"error": "Company and job title are required."}), 400

    if not status:
        return jsonify({"error": "A valid job status is required."}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM jobs
                WHERE id = %s AND user_id = %s
                """,
                (job_id, session["user_id"]),
            )
            job = cursor.fetchone()

            if not job:
                return jsonify({"error": "Job not found."}), 404

            cursor.execute(
                """
                UPDATE jobs
                SET company = %s,
                    title = %s,
                    website = %s,
                    job_link = %s,
                    description = %s,
                    status = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    company,
                    title,
                    website,
                    job_link,
                    description,
                    status,
                    job_id,
                    session["user_id"],
                ),
            )

            cursor.execute(
                """
                SELECT *
                FROM jobs
                WHERE id = %s AND user_id = %s
                """,
                (job_id, session["user_id"]),
            )
            updated_job = cursor.fetchone()

        return jsonify({"message": "Job updated successfully.", "job": updated_job})
    finally:
        conn.close()


@app.delete("/api/jobs/<int:job_id>")
@login_required
def delete_job(job_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM jobs
                WHERE id = %s AND user_id = %s
                """,
                (job_id, session["user_id"]),
            )
            deleted_count = cursor.rowcount

        if deleted_count == 0:
            return jsonify({"error": "Job not found."}), 404

        return jsonify({"message": "Job deleted successfully."})
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=5001)
