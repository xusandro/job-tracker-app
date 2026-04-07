import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as flask_app
from app import validate_birth_date, normalize_job_status


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    with flask_app.app.test_client() as c:
        yield c


def make_mock_conn(fetchone=None, fetchall=None, rowcount=1, lastrowid=1):
    """Build a mock connection that works as a context manager."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = fetchone
    mock_cursor.fetchall.return_value = fetchall or []
    mock_cursor.rowcount = rowcount
    mock_cursor.lastrowid = lastrowid

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__ = lambda s: mock_cursor
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


def set_session(client, user_id=1, username="testuser"):
    """Log in via the real login endpoint with a mocked DB."""
    hashed = generate_password_hash("password123")
    fake_user = {
        "id": user_id,
        "username": username,
        "password_hash": hashed,
    }
    with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=fake_user)):
        client.post(
            "/api/login",
            json={"username": username, "password": "password123"},
        )


# ---------------------------------------------------------------------------
# Unit tests — pure functions, no DB
# ---------------------------------------------------------------------------

class TestValidateBirthDate:
    def test_valid_date(self):
        assert validate_birth_date("1995-06-15") == "1995-06-15"

    def test_invalid_string(self):
        assert validate_birth_date("not-a-date") is None

    def test_wrong_format(self):
        assert validate_birth_date("15/06/1995") is None

    def test_empty_string(self):
        assert validate_birth_date("") is None

    def test_none(self):
        assert validate_birth_date(None) is None


class TestNormalizeJobStatus:
    def test_valid_statuses(self):
        for s in ["in_progress", "interview", "offer", "rejected"]:
            assert normalize_job_status(s) == s

    def test_uppercase_normalized(self):
        assert normalize_job_status("OFFER") == "offer"
        assert normalize_job_status("Interview") == "interview"

    def test_invalid_status(self):
        assert normalize_job_status("pending") is None
        assert normalize_job_status("hired") is None

    def test_empty(self):
        assert normalize_job_status("") == "in_progress"

    def test_none(self):
        assert normalize_job_status(None) == "in_progress"


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# GET /api/session
# ---------------------------------------------------------------------------

class TestSession:
    def test_unauthenticated(self, client):
        res = client.get("/api/session")
        assert res.status_code == 200
        data = res.get_json()
        assert data["authenticated"] is False
        assert data["user"] is None

    def test_authenticated(self, client):
        set_session(client)
        res = client.get("/api/session")
        assert res.status_code == 200
        data = res.get_json()
        assert data["authenticated"] is True
        assert data["user"]["username"] == "testuser"


# ---------------------------------------------------------------------------
# POST /api/register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_missing_fields(self, client):
        res = client.post("/api/register", json={})
        assert res.status_code == 400

    def test_missing_birth_date(self, client):
        res = client.post("/api/register", json={"username": "u", "password": "pass123"})
        assert res.status_code == 400

    def test_short_password(self, client):
        res = client.post(
            "/api/register",
            json={"username": "u", "password": "abc", "birth_date": "1995-01-01"},
        )
        assert res.status_code == 400

    def test_invalid_birth_date(self, client):
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=None)):
            res = client.post(
                "/api/register",
                json={"username": "u", "password": "pass123", "birth_date": "not-a-date"},
            )
        assert res.status_code == 400

    def test_duplicate_username(self, client):
        with patch(
            "app.get_db_connection",
            return_value=make_mock_conn(fetchone={"id": 99}),
        ):
            res = client.post(
                "/api/register",
                json={"username": "existing", "password": "pass123", "birth_date": "1995-01-01"},
            )
        assert res.status_code == 409

    def test_success(self, client):
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=None)):
            res = client.post(
                "/api/register",
                json={"username": "newuser", "password": "pass123", "birth_date": "1995-01-01"},
            )
        assert res.status_code == 201


# ---------------------------------------------------------------------------
# POST /api/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_user_not_found(self, client):
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=None)):
            res = client.post("/api/login", json={"username": "x", "password": "y"})
        assert res.status_code == 401

    def test_wrong_password(self, client):
        fake_user = {"id": 1, "username": "u", "password_hash": generate_password_hash("correct")}
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=fake_user)):
            res = client.post("/api/login", json={"username": "u", "password": "wrong"})
        assert res.status_code == 401

    def test_success(self, client):
        hashed = generate_password_hash("pass123")
        fake_user = {"id": 1, "username": "alice", "password_hash": hashed}
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=fake_user)):
            res = client.post("/api/login", json={"username": "alice", "password": "pass123"})
        assert res.status_code == 200
        assert res.get_json()["user"]["username"] == "alice"


# ---------------------------------------------------------------------------
# POST /api/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_not_authenticated(self, client):
        res = client.post("/api/logout")
        assert res.status_code == 401

    def test_authenticated(self, client):
        set_session(client)
        res = client.post("/api/logout")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_not_authenticated(self, client):
        res = client.get("/api/jobs")
        assert res.status_code == 401

    def test_empty_list(self, client):
        set_session(client)
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchall=[])):
            res = client.get("/api/jobs")
        assert res.status_code == 200
        assert res.get_json()["jobs"] == []

    def test_returns_jobs(self, client):
        set_session(client)
        fake_jobs = [
            {"id": 1, "company": "Acme", "title": "Dev", "status": "in_progress"},
        ]
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchall=fake_jobs)):
            res = client.get("/api/jobs")
        assert res.status_code == 200
        assert len(res.get_json()["jobs"]) == 1


# ---------------------------------------------------------------------------
# POST /api/jobs
# ---------------------------------------------------------------------------

class TestCreateJob:
    def test_not_authenticated(self, client):
        res = client.post("/api/jobs", json={})
        assert res.status_code == 401

    def test_missing_company(self, client):
        set_session(client)
        res = client.post("/api/jobs", json={"title": "Dev", "status": "in_progress"})
        assert res.status_code == 400

    def test_missing_title(self, client):
        set_session(client)
        res = client.post("/api/jobs", json={"company": "Acme", "status": "in_progress"})
        assert res.status_code == 400

    def test_invalid_status(self, client):
        set_session(client)
        res = client.post(
            "/api/jobs",
            json={"company": "Acme", "title": "Dev", "status": "hired"},
        )
        assert res.status_code == 400

    def test_success(self, client):
        set_session(client)
        new_job = {"id": 1, "company": "Acme", "title": "Dev", "status": "in_progress"}
        mock_conn = make_mock_conn(fetchone=new_job, lastrowid=1)
        with patch("app.get_db_connection", return_value=mock_conn):
            res = client.post(
                "/api/jobs",
                json={"company": "Acme", "title": "Dev", "status": "in_progress"},
            )
        assert res.status_code == 201
        assert res.get_json()["job"]["company"] == "Acme"


# ---------------------------------------------------------------------------
# GET /api/jobs/<id>
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_not_authenticated(self, client):
        res = client.get("/api/jobs/1")
        assert res.status_code == 401

    def test_not_found(self, client):
        set_session(client)
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=None)):
            res = client.get("/api/jobs/999")
        assert res.status_code == 404

    def test_found(self, client):
        set_session(client)
        fake_job = {"id": 1, "company": "Acme", "title": "Dev", "status": "offer"}
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=fake_job)):
            res = client.get("/api/jobs/1")
        assert res.status_code == 200
        assert res.get_json()["job"]["company"] == "Acme"


# ---------------------------------------------------------------------------
# PUT /api/jobs/<id>
# ---------------------------------------------------------------------------

class TestUpdateJob:
    def test_not_authenticated(self, client):
        res = client.put("/api/jobs/1", json={})
        assert res.status_code == 401

    def test_missing_fields(self, client):
        set_session(client)
        res = client.put("/api/jobs/1", json={"status": "offer"})
        assert res.status_code == 400

    def test_invalid_status(self, client):
        set_session(client)
        res = client.put(
            "/api/jobs/1",
            json={"company": "Acme", "title": "Dev", "status": "bad"},
        )
        assert res.status_code == 400

    def test_not_found(self, client):
        set_session(client)
        with patch("app.get_db_connection", return_value=make_mock_conn(fetchone=None)):
            res = client.put(
                "/api/jobs/999",
                json={"company": "Acme", "title": "Dev", "status": "offer"},
            )
        assert res.status_code == 404

    def test_success(self, client):
        set_session(client)
        existing = {"id": 1}
        updated = {"id": 1, "company": "Acme", "title": "Dev", "status": "offer"}

        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [existing, updated]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch("app.get_db_connection", return_value=mock_conn):
            res = client.put(
                "/api/jobs/1",
                json={"company": "Acme", "title": "Dev", "status": "offer"},
            )
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/jobs/<id>
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_not_authenticated(self, client):
        res = client.delete("/api/jobs/1")
        assert res.status_code == 401

    def test_not_found(self, client):
        set_session(client)
        with patch("app.get_db_connection", return_value=make_mock_conn(rowcount=0)):
            res = client.delete("/api/jobs/999")
        assert res.status_code == 404

    def test_success(self, client):
        set_session(client)
        with patch("app.get_db_connection", return_value=make_mock_conn(rowcount=1)):
            res = client.delete("/api/jobs/1")
        assert res.status_code == 200
        assert "deleted" in res.get_json()["message"].lower()
