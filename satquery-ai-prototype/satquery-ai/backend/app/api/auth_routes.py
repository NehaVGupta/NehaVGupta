import logging
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field, field_validator

from app import deps
from app.api.security import require_allowed_origin, require_authenticated, require_csrf
from app.config.settings import settings
from app.services.auth_service import validate_email
from app.utils.errors import UserError

log = logging.getLogger("satquery.auth")
router = APIRouter(prefix="/api/auth", tags=["authentication"])
RESET_CONFIRMATION = "If an account exists for this email, a password reset link has been sent."


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
    confirm_password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return validate_email(value)

    @field_validator("full_name")
    @classmethod
    def valid_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Full name is required.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return validate_email(value)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return validate_email(value)


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=1, max_length=128)
    confirm_password: str = Field(min_length=1, max_length=128)


def _set_session_cookies(response, session):
    max_age = session["max_age"] if session["remember_me"] else None
    response.set_cookie(settings.auth_session_cookie, session["token"], max_age=max_age, httponly=True,
                        secure=settings.auth_cookie_secure, samesite="lax", path="/")
    response.set_cookie(settings.auth_csrf_cookie, session["csrf_token"], max_age=max_age,
                        httponly=False, secure=settings.auth_cookie_secure, samesite="lax", path="/")


def _clear_session_cookies(response):
    response.delete_cookie(settings.auth_session_cookie, path="/", secure=settings.auth_cookie_secure, httponly=True, samesite="lax")
    response.delete_cookie(settings.auth_csrf_cookie, path="/", secure=settings.auth_cookie_secure, httponly=False, samesite="lax")


def _send_reset_email(recipient, name, token):
    if not settings.smtp_host or not settings.smtp_from:
        log.warning("Password reset email is not configured; no reset link was sent.")
        return
    reset_url = f"{settings.auth_frontend_url.rstrip('/')}/reset-password?{urlencode({'token': token})}"
    message = EmailMessage()
    message["Subject"] = "Reset your SatQuery AI password"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(f"Hello {name},\n\nUse this one-time link to reset your SatQuery AI password. It expires in {settings.auth_reset_token_minutes} minutes.\n\n{reset_url}\n\nIf you did not request this, you can ignore this message.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        if settings.smtp_starttls:
            server.starttls(context=ssl.create_default_context())
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


@router.post("/register", status_code=201, dependencies=[Depends(require_allowed_origin)])
def register(req: RegisterRequest):
    if req.password != req.confirm_password:
        raise UserError("Passwords do not match.", "password_mismatch", 422)
    return {"user": deps.auth.register(req.full_name, req.email, req.password)}


@router.post("/login", dependencies=[Depends(require_allowed_origin)])
def login(req: LoginRequest, response: Response):
    user = deps.auth.login(req.email, req.password)
    _set_session_cookies(response, deps.auth.create_session(user, req.remember_me))
    return {"user": user}


@router.post("/logout", dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(require_allowed_origin)])
def logout(request: Request, response: Response):
    deps.auth.logout(request.cookies.get(settings.auth_session_cookie))
    _clear_session_cookies(response)
    return {"ok": True}


@router.get("/me")
def current_user(user=Depends(require_authenticated)):
    return {"user": user}


@router.post("/forgot-password", dependencies=[Depends(require_allowed_origin)])
def forgot_password(req: ForgotPasswordRequest):
    reset = deps.auth.issue_reset_token(req.email)
    if reset:
        try:
            _send_reset_email(reset["email"], reset["name"], reset["token"])
        except Exception:  # noqa: BLE001
            log.warning("Password reset email delivery failed.")
    return {"message": RESET_CONFIRMATION}


@router.post("/reset-password", dependencies=[Depends(require_allowed_origin)])
def reset_password(req: ResetPasswordRequest):
    if req.new_password != req.confirm_password:
        raise UserError("Passwords do not match.", "password_mismatch", 422)
    user = deps.auth.reset_password(req.token, req.new_password)
    return {"message": "Your password has been reset successfully.", "user": user}