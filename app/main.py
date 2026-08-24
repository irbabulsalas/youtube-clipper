from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import clip, health, auth as auth_router, admin
from app.database import get_db
from app.auth import init_owner_account

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