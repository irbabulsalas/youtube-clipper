from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import clip, health, auth as auth_router, admin
from app.database import get_db
from app.auth import init_owner_account
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Clipper",
    description="Auto-generate clips from YouTube videos with subtitles",
    version="0.1.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(auth_router.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(clip.router, prefix="/api", tags=["clip"])

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_event():
    db = next(get_db())
    init_owner_account(db)
    # Preload Whisper model during startup to avoid OOM mid-job
    try:
        from app.services.transcriber import transcriber
        logger.info("Preloading Whisper tiny model...")
        # Touch the model property to trigger load
        _ = transcriber.model
        logger.info("Whisper model preloaded successfully")
    except Exception as e:
        logger.warning(f"Whisper model preload failed: {e} - will retry on first job")


@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("static/login.html")


@app.get("/login.html", response_class=FileResponse)
async def login_page():
    return FileResponse("static/login.html")


@app.get("/index.html", response_class=FileResponse)
async def main_page():
    return FileResponse("static/index.html")


@app.get("/menu.html", response_class=FileResponse)
async def menu_page():
    return FileResponse("static/menu.html")


@app.get("/admin.html", response_class=FileResponse)
async def admin_page():
    return FileResponse("static/admin.html")