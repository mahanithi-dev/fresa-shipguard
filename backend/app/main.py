import logging
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.routers import admin, ai, auth, external_router, reference, reports, risk, shipments
from app.seed import seed_demo_data
from app.services.external_data import sync_all_external_data
from app.services.retrieval import build_index
from app.services.scoring_service import score_active_shipments
from app.services.security import log_security_event

logger = logging.getLogger("shipguard.main")
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects industry-standard HTTP security headers to protect against common web attacks."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* https:; "
            "font-src 'self' data:; "
            "frame-ancestors 'self';"
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    Base.metadata.create_all(bind=engine)
    if os.environ.get("TESTING") != "1":
        db = SessionLocal()
        try:
            seed_demo_data(db)
            try:
                sync_all_external_data(db, force=False)
            except Exception as exc:
                logger.warning("External data sync notice: %s", exc)
            score_active_shipments(db)
            try:
                build_index(db)
            except Exception as exc:
                logger.warning("Retrieval index build notice: %s", exc)
        finally:
            db.close()
    yield
    # Shutdown tasks (if any)


app = FastAPI(title="ShipGuard API", version="1.0.0", lifespan=lifespan)

# Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS Configuration: strictly enforce valid origins
configured_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
default_safe_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176",
]
allowed_origins = configured_origins if configured_origins else default_safe_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler preventing internal stack trace and database error leakage."""
    client_ip = request.client.host if request.client else "unknown"
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )

    # Log full traceback securely on server side
    logger.error("Unhandled Exception on %s %s: %s\n%s", request.method, request.url.path, exc, traceback.format_exc())
    log_security_event("UNHANDLED_EXCEPTION", f"{request.method} {request.url.path}: {type(exc).__name__}", client_ip=client_ip)

    # Return safe generic error message to the client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(reference.router, prefix="/api/v1")
app.include_router(shipments.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(external_router.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve built frontend so API and SPA share the same origin
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
index_file = frontend_dist / "index.html"
if frontend_dist.exists() and index_file.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    def spa_index():
        return FileResponse(str(index_file))

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_catchall(full_path: str):
        if full_path.startswith("api/") or full_path == "health":
            raise HTTPException(status_code=404)
        return FileResponse(str(index_file))

