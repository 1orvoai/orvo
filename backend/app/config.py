"""
ORVO configuration.
All secrets/config come from environment variables (.env file locally).
Nothing here is hard-coded — copy .env.example to .env and fill in real values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(val: str, default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


class Settings:
    # --- App ---
    APP_NAME: str = "ORVO"
    ENV: str = os.getenv("ENV", "development")
    DEBUG: bool = _bool(os.getenv("DEBUG"), True)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8000")

    # --- Database ---
    # Defaults to local SQLite file. Set DATABASE_URL to a postgres:// URL
    # (e.g. postgresql+psycopg2://user:pass@host:5432/orvo) to use PostgreSQL instead.
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'orvo.db'}")

    # --- Security / JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_INSECURE_DEFAULT_DEV_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "525600"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "365"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))

    # --- CORS ---
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

    # --- Rate limiting ---
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
    RATE_LIMIT_AUTH: str = os.getenv("RATE_LIMIT_AUTH", "10/minute")

    # --- Email (SMTP) — required for real password-reset emails to send ---
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "no-reply@orvo.local")
    SMTP_USE_TLS: bool = _bool(os.getenv("SMTP_USE_TLS"), True)

    # --- Market data (Binance public API — no key required) ---
    BINANCE_REST_URL: str = os.getenv("BINANCE_REST_URL", "https://api.binance.com")
    BINANCE_WS_URL: str = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443")
    DEFAULT_SYMBOLS: list = os.getenv("DEFAULT_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT").split(",")

    # --- News / economic calendar (optional — requires your own API key) ---
    # Get a free key at https://financialmodelingprep.com or https://finnhub.io
    NEWS_API_PROVIDER: str = os.getenv("NEWS_API_PROVIDER", "")  # "fmp" or "finnhub" or ""
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")

    # --- MT5 broker integration ---
    # The MetaTrader5 python package only works on Windows with a MT5 terminal installed.
    # Credentials are supplied per-user at runtime via the /broker/mt5/connect endpoint,
    # never stored in this file.
    MT5_TERMINAL_PATH: str = os.getenv("MT5_TERMINAL_PATH", "")

    # --- Admin ---
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@orvo.local")


settings = Settings()
