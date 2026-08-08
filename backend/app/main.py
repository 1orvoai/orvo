from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .database import Base, engine
from .models import User, UserRole
from .security import hash_password
from .database import SessionLocal
from .routers import admin, ai_engine, auth, broker, dashboard, market, news, risk, trading, users, websocket

# --- DB bootstrap ---
Base.metadata.create_all(bind=engine)

# Seed a default admin account on first run if none exists (dev convenience,
# password must be changed immediately — printed once to console, never hard-coded).
def _seed_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
        if not existing_admin:
            import secrets
            temp_password = secrets.token_urlsafe(12)
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                full_name="ORVO Admin",
                hashed_password=hash_password(temp_password),
                role=UserRole.admin,
            )
            db.add(admin_user)
            db.commit()
            print("=" * 70)
            print(f"[ORVO] First-run admin account created:")
            print(f"        email:    {settings.ADMIN_EMAIL}")
            print(f"        password: {temp_password}")
            print("        Log in and change this password immediately.")
            print("=" * 70)
    finally:
        db.close()


_seed_admin()

# --- App ---
app = FastAPI(title="ORVO Trading Platform", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://s3.tradingview.com https://cdn.jsdelivr.net 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.binance.com wss://stream.binance.com ws: wss:; "
        "frame-src https://s.tradingview.com;"
    )
    if settings.ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error." if not settings.DEBUG else str(exc)})


# --- API routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(trading.router)
app.include_router(broker.router)
app.include_router(market.router)
app.include_router(ai_engine.router)
app.include_router(risk.router)
app.include_router(news.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "ORVO"}


# --- Frontend (static files) ---
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/{page_name}.html")
    async def serve_page(page_name: str):
        file_path = FRONTEND_DIR / f"{page_name}.html"
        if file_path.exists():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
