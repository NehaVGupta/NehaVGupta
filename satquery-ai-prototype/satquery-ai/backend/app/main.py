import logging

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth_routes import router as auth_router
from app.api.routes import public_router, router
from app.api.security import require_authenticated, require_csrf
from app.config.settings import settings
from app.utils.errors import UserError

log = logging.getLogger("satquery")
app = FastAPI(title="SatQuery AI API", version=settings.version, description="Evidence-grounded natural-language analysis of satellite imagery (SIH 2026 prototype).")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["GET", "POST"], allow_headers=["*"], allow_credentials=True)


def _err(status, code, message):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(UserError)
async def user_error(_: Request, e: UserError):
    return _err(e.status, e.code, e.message)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, e: RequestValidationError):
    return _err(422, "invalid_request", "The request was invalid. Please check the question and selected images.")


@app.exception_handler(Exception)
async def unexpected(_: Request, e: Exception):
    log.exception("Unhandled error")  # stack trace stays in server logs only
    return _err(500, "analysis_failed", "The analysis could not be completed. Please try again or use a different image.")


app.include_router(auth_router)
app.include_router(public_router)
app.include_router(router, dependencies=[Depends(require_authenticated), Depends(require_csrf)])
if settings.static_dir.exists():
    app.mount("/assets", StaticFiles(directory=settings.static_dir / "assets"), name="assets")
    app.mount("/samples", StaticFiles(directory=settings.static_dir / "samples"), name="samples")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):  # noqa: ARG001 — React Router client-side routes fall back to index.html
        return FileResponse(settings.static_dir / "index.html")
