from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
from pathlib import Path

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.routers import admin, ai, auth, external_router, reference, reports, risk, shipments
from app.seed import seed_demo_data
from app.services.external_data import sync_all_external_data
from app.services.retrieval import build_index
from app.services.scoring_service import score_active_shipments


settings = get_settings()
app = FastAPI(title="ShipGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(reference.router, prefix="/api/v1")
app.include_router(shipments.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(external_router.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


# Serve built frontend so API and SPA share the same origin (avoids CORS/relative fetch issues)
frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
index_file = frontend_dist / "index.html"
if frontend_dist.exists() and index_file.exists():
    # serve static assets under /assets and return index.html for SPA routes
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    def spa_index():
        return FileResponse(str(index_file))

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_catchall(full_path: str):
        # allow API routes to be handled by routers
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        return FileResponse(str(index_file))


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
        try:
            sync_all_external_data(db, force=False)
        except Exception as exc:
            print("External data sync notice:", exc)
        score_active_shipments(db)
        # build retrieval index for RAG
        try:
            build_index(db)
        except Exception:
            pass
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}
