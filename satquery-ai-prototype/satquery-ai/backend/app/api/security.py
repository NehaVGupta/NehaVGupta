import hmac

from fastapi import Request

from app import deps
from app.config.settings import settings
from app.utils.errors import UserError


def require_authenticated(request: Request):
    token = request.cookies.get(settings.auth_session_cookie)
    user, _ = deps.auth.authenticate(token)
    request.state.auth_user = user
    return user


def require_csrf(request: Request):
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    token = request.cookies.get(settings.auth_session_cookie)
    csrf_cookie = request.cookies.get(settings.auth_csrf_cookie, "")
    csrf_header = request.headers.get("x-csrf-token", "")
    if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header) or not deps.auth.validate_csrf(token, csrf_header):
        raise UserError("Your session could not be verified. Please sign in again.", "csrf_failed", 403)


def require_allowed_origin(request: Request):
    origin = request.headers.get("origin")
    allowed = {item.rstrip("/") for item in settings.cors_origins}
    if origin and origin.rstrip("/") not in allowed:
        raise UserError("This request origin is not allowed.", "origin_not_allowed", 403)