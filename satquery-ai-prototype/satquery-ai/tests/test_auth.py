import hashlib
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app import deps
from app.api import auth_routes
from app.config.settings import settings
from app.main import app


def test_register_login_and_duplicate_email(client):
    payload = {"full_name": "Example User", "email": "Example.User@example.com",
               "password": "Test@1234", "confirm_password": "Test@1234"}
    registered = client.post("/api/auth/register", json=payload)
    assert registered.status_code == 201
    user = registered.json()["user"]
    assert user["email"] == "example.user@example.com"
    assert "password" not in user and "password_hash" not in user

    stored = deps.repo.get("auth_users", user["id"])
    assert stored["password_hash"].startswith("scrypt$")
    assert "password" not in stored
    assert client.post("/api/auth/register", json=payload).status_code == 409
    assert client.post("/api/auth/login", json={"email": user["email"], "password": "Wrong@1234"}).status_code == 401

    logged_in = TestClient(app)
    response = logged_in.post("/api/auth/login", json={"email": user["email"], "password": payload["password"], "remember_me": True})
    assert response.status_code == 200
    assert response.json()["user"]["id"] == user["id"]
    assert logged_in.cookies.get(settings.auth_session_cookie)
    assert "httponly" in response.headers["set-cookie"].lower()
    assert logged_in.get("/api/auth/me").json()["user"]["email"] == user["email"]


def test_auth_validation_and_unauthorized_routes():
    client = TestClient(app)
    assert client.get("/api/stats").status_code == 401
    assert client.get("/api/health").status_code == 200
    assert client.post("/api/auth/register", json={"full_name": "Test", "email": "bad", "password": "Test@1234", "confirm_password": "Test@1234"}).status_code == 422
    assert client.post("/api/auth/register", json={"full_name": "Test", "email": "valid@example.com", "password": "weak", "confirm_password": "weak"}).status_code == 422
    assert client.post("/api/auth/register", json={"full_name": "Test", "email": "valid@example.com", "password": "Test@1234", "confirm_password": "Other@1234"}).status_code == 422


def test_csrf_logout_and_protected_api():
    client = TestClient(app)
    payload = {"full_name": "Session User", "email": "session.user@example.com",
               "password": "Test@1234", "confirm_password": "Test@1234"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 200
    assert client.post("/api/demo/load/urban").status_code == 403
    client.headers.update({"x-csrf-token": client.cookies.get(settings.auth_csrf_cookie)})
    assert client.post("/api/demo/load/urban").status_code == 200
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/stats").status_code == 401


def test_forgot_reset_generic_response_and_one_time_token(client, monkeypatch):
    email = "reset.user@example.com"
    registered = client.post("/api/auth/register", json={"full_name": "Reset User", "email": email,
                                                         "password": "Test@1234", "confirm_password": "Test@1234"})
    assert registered.status_code == 201
    tokens = []
    monkeypatch.setattr(auth_routes, "_send_reset_email", lambda recipient, name, token: tokens.append(token))

    known = client.post("/api/auth/forgot-password", json={"email": email})
    unknown = client.post("/api/auth/forgot-password", json={"email": "missing@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    assert len(tokens) == 1

    mismatch = client.post("/api/auth/reset-password", json={"token": tokens[0], "new_password": "New@Password1", "confirm_password": "Other@Password1"})
    assert mismatch.status_code == 422
    reset = client.post("/api/auth/reset-password", json={"token": tokens[0], "new_password": "New@Password1", "confirm_password": "New@Password1"})
    assert reset.status_code == 200
    assert reset.json()["message"] == "Your password has been reset successfully."
    assert deps.auth.login(email, "New@Password1")["email"] == email
    assert client.post("/api/auth/reset-password", json={"token": tokens[0], "new_password": "New@Password1", "confirm_password": "New@Password1"}).status_code == 400


def test_reset_token_expiry(client):
    token_data = deps.auth.issue_reset_token("test.user@example.com")
    token_hash = hashlib.sha256(token_data["token"].encode("utf-8")).hexdigest()
    record = deps.repo.get("auth_resets", token_hash)
    record["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    deps.repo.put("auth_resets", token_hash, record)
    expired = client.post("/api/auth/reset-password", json={"token": token_data["token"], "new_password": "New@Password1", "confirm_password": "New@Password1"})
    assert expired.status_code == 400


def test_expired_session_is_rejected():
    client = TestClient(app)
    payload = {"full_name": "Expiry User", "email": "expiry.user@example.com",
               "password": "Test@1234", "confirm_password": "Test@1234"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]}).status_code == 200
    token = client.cookies.get(settings.auth_session_cookie)
    session_id = hashlib.sha256(token.encode("utf-8")).hexdigest()
    session = deps.repo.get("auth_sessions", session_id)
    session["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    deps.repo.put("auth_sessions", session_id, session)
    assert client.get("/api/auth/me").status_code == 401


def test_password_reset_revokes_existing_sessions(monkeypatch):
    client = TestClient(app)
    email = "revoke.session@example.com"
    password = "Test@1234"
    registered = client.post("/api/auth/register", json={"full_name": "Reset Session", "email": email,
                                                         "password": password, "confirm_password": password})
    assert registered.status_code == 201
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200
    tokens = []
    monkeypatch.setattr(auth_routes, "_send_reset_email", lambda recipient, name, token: tokens.append(token))
    assert client.post("/api/auth/forgot-password", json={"email": email}).status_code == 200
    reset_password = "Next@Password1"
    assert client.post("/api/auth/reset-password", json={"token": tokens[0], "new_password": reset_password,
                                                         "confirm_password": reset_password}).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_accounts_have_private_images_history_and_stats():
    def create_account(name, email):
        account = TestClient(app)
        password = "Test@1234"
        created = account.post("/api/auth/register", json={"full_name": name, "email": email,
                                                            "password": password, "confirm_password": password})
        assert created.status_code == 201
        logged_in = account.post("/api/auth/login", json={"email": email, "password": password})
        assert logged_in.status_code == 200
        account.headers.update({"x-csrf-token": account.cookies.get(settings.auth_csrf_cookie)})
        return account

    alice = create_account("Alice Analyst", "alice.isolation@example.com")
    bob = create_account("Bob Analyst", "bob.isolation@example.com")
    sample = alice.post("/api/demo/load/urban").json()
    demo_image_id = sample["images"][0]["id"]

    alice_query = alice.post("/api/query", json={"query": "How many buildings are visible?", "image_id": demo_image_id})
    assert alice_query.status_code == 200
    alice_analysis_id = alice_query.json()["id"]
    assert alice.get("/api/history").json()[0]["id"] == alice_analysis_id
    assert bob.get("/api/history").json() == []
    assert alice.get("/api/stats").json()["queries_executed"] == 1
    bob_stats = bob.get("/api/stats")
    assert bob_stats.status_code == 200, bob_stats.text
    assert bob_stats.json()["queries_executed"] == 0
    assert bob.get(f"/api/analysis/{alice_analysis_id}").status_code == 404
    assert bob.get(f"/api/analysis/{alice_analysis_id}/geojson").status_code == 404
    assert bob.get(f"/api/report/{alice_analysis_id}").status_code == 404
    assert "owner_user_id" not in alice.get("/api/history").json()[0]

    uploaded_png = deps.images.png_bytes(demo_image_id)
    upload = alice.post("/api/upload", files={"file": ("private.png", uploaded_png, "image/png")})
    assert upload.status_code == 200
    private_image_id = upload.json()["id"]
    assert alice.get(f"/api/image/{private_image_id}").status_code == 200
    assert bob.get(f"/api/image/{private_image_id}").status_code == 404
    assert bob.post("/api/query", json={"query": "Describe this image", "image_id": private_image_id}).status_code == 404

    bob_query = bob.post("/api/query", json={"query": "Show me the water bodies", "image_id": demo_image_id})
    assert bob_query.status_code == 200
    bob_analysis_id = bob_query.json()["id"]
    assert [item["id"] for item in bob.get("/api/history").json()] == [bob_analysis_id]
    assert [item["id"] for item in alice.get("/api/history").json()] == [alice_analysis_id]