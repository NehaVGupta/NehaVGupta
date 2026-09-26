"""Account, scrypt password, reset-token, and opaque session handling."""
import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from threading import RLock

from app.config.settings import settings
from app.utils.errors import UserError

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SPECIAL = re.compile(r"[^A-Za-z0-9]")
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def normalize_email(email):
    return email.strip().lower()


def validate_email(email):
    if not _EMAIL.fullmatch(email.strip()):
        raise UserError("Please enter a valid email address.", "invalid_email", 422)
    return normalize_email(email)


def password_requirements(password):
    return {
        "length": len(password) >= 8,
        "uppercase": any(char.isupper() for char in password),
        "lowercase": any(char.islower() for char in password),
        "number": any(char.isdigit() for char in password),
        "special": bool(_SPECIAL.search(password)),
    }


def validate_password(password):
    if len(password) > 128 or not all(password_requirements(password).values()):
        raise UserError("Password must contain 8 characters, uppercase and lowercase letters, a number, and a special character.", "weak_password", 422)


def _b64encode(value):
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _token_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc)


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P, dklen=32)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password, encoded):
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        expected_bytes = _b64decode(expected)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=_b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=len(expected_bytes))
        return hmac.compare_digest(actual, expected_bytes)
    except (ValueError, TypeError, MemoryError):
        return False


_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(24))


class AuthService:
    def __init__(self, repository):
        self.repo = repository
        self.lock = RLock()

    @staticmethod
    def public_user(user):
        return {key: user[key] for key in ("id", "name", "email", "created_at")}

    def _user_by_email(self, email):
        return next((user for user in self.repo.list("auth_users") if user["email"] == email), None)

    def _user_by_id(self, user_id):
        if not self.repo.exists("auth_users", user_id):
            return None
        return self.repo.get("auth_users", user_id)

    def register(self, name, email, password):
        name, email = name.strip(), validate_email(email)
        if not name:
            raise UserError("Full name is required.", "invalid_name", 422)
        validate_password(password)
        with self.lock:
            if self._user_by_email(email):
                raise UserError("An account with this email already exists.", "email_registered", 409)
            now = _now().isoformat()
            user = {"id": secrets.token_urlsafe(18), "name": name, "email": email,
                    "password_hash": hash_password(password), "created_at": now, "updated_at": now}
            self.repo.put("auth_users", user["id"], user)
        return self.public_user(user)

    def login(self, email, password):
        user = self._user_by_email(validate_email(email))
        encoded = user["password_hash"] if user else _DUMMY_PASSWORD_HASH
        valid = verify_password(password, encoded)
        if not user or not valid:
            raise UserError("Email or password is incorrect.", "invalid_credentials", 401)
        return self.public_user(user)

    def create_session(self, user, remember_me=False):
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        lifetime = timedelta(days=settings.auth_remember_days) if remember_me else timedelta(hours=settings.auth_session_hours)
        session_id = _token_hash(token)
        session = {"id": session_id, "user_id": user["id"], "csrf_hash": _token_hash(csrf),
                   "expires_at": (_now() + lifetime).isoformat(), "revoked": False}
        self.repo.put("auth_sessions", session_id, session)
        return {"token": token, "csrf_token": csrf, "max_age": int(lifetime.total_seconds()), "remember_me": remember_me}

    def authenticate(self, token):
        session_id = _token_hash(token) if token else ""
        if not session_id or not self.repo.exists("auth_sessions", session_id):
            raise UserError("Please sign in to continue.", "unauthorized", 401)
        session = self.repo.get("auth_sessions", session_id)
        if session.get("revoked") or datetime.fromisoformat(session["expires_at"]) <= _now():
            raise UserError("Your session has expired. Please sign in again.", "unauthorized", 401)
        user = self._user_by_id(session["user_id"])
        if not user:
            raise UserError("Your session is no longer valid. Please sign in again.", "unauthorized", 401)
        return self.public_user(user), session

    def validate_csrf(self, token, csrf):
        session_id = _token_hash(token) if token else ""
        if not session_id or not self.repo.exists("auth_sessions", session_id):
            return False
        session = self.repo.get("auth_sessions", session_id)
        return (not session.get("revoked") and datetime.fromisoformat(session["expires_at"]) > _now()
                and hmac.compare_digest(session.get("csrf_hash", ""), _token_hash(csrf or "")))

    def logout(self, token):
        session_id = _token_hash(token) if token else ""
        with self.lock:
            if session_id and self.repo.exists("auth_sessions", session_id):
                session = self.repo.get("auth_sessions", session_id)
                session["revoked"] = True
                self.repo.put("auth_sessions", session_id, session)

    def issue_reset_token(self, email):
        user = self._user_by_email(validate_email(email))
        if not user:
            return None
        token = secrets.token_urlsafe(32)
        token_hash = _token_hash(token)
        reset = {"id": token_hash, "user_id": user["id"],
                 "expires_at": (_now() + timedelta(minutes=settings.auth_reset_token_minutes)).isoformat(), "used": False}
        self.repo.put("auth_resets", token_hash, reset)
        return {"name": user["name"], "email": user["email"], "token": token}

    def reset_password(self, token, password):
        validate_password(password)
        token_hash = _token_hash(token)
        with self.lock:
            if not self.repo.exists("auth_resets", token_hash):
                raise UserError("This reset link is invalid or expired. Request a new one.", "invalid_reset_token", 400)
            reset = self.repo.get("auth_resets", token_hash)
            if reset.get("used") or datetime.fromisoformat(reset["expires_at"]) <= _now():
                raise UserError("This reset link is invalid or expired. Request a new one.", "invalid_reset_token", 400)
            user = self._user_by_id(reset["user_id"])
            if not user:
                raise UserError("This reset link is invalid or expired. Request a new one.", "invalid_reset_token", 400)
            user["password_hash"] = hash_password(password)
            user["updated_at"] = _now().isoformat()
            self.repo.put("auth_users", user["id"], user)
            reset["used"] = True
            self.repo.put("auth_resets", token_hash, reset)
            for session in self.repo.list("auth_sessions"):
                if session.get("user_id") == user["id"] and not session.get("revoked"):
                    session["revoked"] = True
                    self.repo.put("auth_sessions", session["id"], session)
        return self.public_user(user)