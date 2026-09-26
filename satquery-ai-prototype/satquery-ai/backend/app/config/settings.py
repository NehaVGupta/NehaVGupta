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
    cors_origins = [o.strip() for o in _env("SATQUERY_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000").split(",") if o.strip()]
    redis_url = _env("REDIS_URL", "")
    storage_backend = _env("STORAGE_BACKEND", "local")
    # engine selection: "demo" is the default; real adapters are opt-in (see docs/architecture.md)
    detector = _env("SATQUERY_DETECTOR", "demo")
    segmenter = _env("SATQUERY_SEGMENTER", "demo")
    change_detector = _env("SATQUERY_CHANGE_DETECTOR", "demo")
    static_dir = Path(_env("SATQUERY_STATIC_DIR", str(Path(__file__).resolve().parents[1] / "static")))


settings = Settings()
