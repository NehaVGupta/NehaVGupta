"""Central configuration (environment variables, see .env.example)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _env(name, default):
    return os.getenv(name, default)


class Settings:
    app_name = "SatQuery AI"
    version = "0.1.0-prototype"
    data_dir = Path(_env("SATQUERY_DATA_DIR", str(ROOT / "demo" / "outputs")))
    demo_dir = Path(_env("SATQUERY_DEMO_DIR", str(ROOT / "demo" / "datasets")))
    max_upload_mb = int(_env("SATQUERY_MAX_UPLOAD_MB", "50"))
    max_dim = int(_env("SATQUERY_MAX_DIM", "1600"))
    allowed_ext = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
    cors_origins = [o.strip() for o in _env("SATQUERY_CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000").split(",") if o.strip()]
    redis_url = _env("REDIS_URL", "")
    storage_backend = _env("STORAGE_BACKEND", "local")
    auth_session_cookie = _env("AUTH_SESSION_COOKIE", "satquery_session")
    auth_csrf_cookie = _env("AUTH_CSRF_COOKIE", "satquery_csrf")
    auth_cookie_secure = _env("AUTH_COOKIE_SECURE", "false").lower() == "true"
    auth_session_hours = int(_env("AUTH_SESSION_HOURS", "12"))
    auth_remember_days = int(_env("AUTH_REMEMBER_DAYS", "30"))
    auth_reset_token_minutes = int(_env("AUTH_RESET_TOKEN_MINUTES", "30"))
    auth_frontend_url = _env("AUTH_FRONTEND_URL", "http://localhost:5173")
    smtp_host = _env("SMTP_HOST", "")
    smtp_port = int(_env("SMTP_PORT", "587"))
    smtp_user = _env("SMTP_USER", "")
    smtp_password = _env("SMTP_PASSWORD", "")
    smtp_from = _env("SMTP_FROM", "")
    smtp_starttls = _env("SMTP_STARTTLS", "true").lower() == "true"
    # engine selection: "demo" is the default; real adapters are opt-in (see docs/architecture.md)
    detector = _env("SATQUERY_DETECTOR", "demo")
    segmenter = _env("SATQUERY_SEGMENTER", "demo")
    change_detector = _env("SATQUERY_CHANGE_DETECTOR", "demo")
    static_dir = Path(_env("SATQUERY_STATIC_DIR", str(Path(__file__).resolve().parents[1] / "static")))


settings = Settings()
