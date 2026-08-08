# Installation Guide

## Prerequisites

- Python 3.11+ (3.10 also works)
- pip
- Git
- (Optional) Docker + Docker Compose
- (Optional, for live MT5 trading) Windows + a MetaTrader 5 terminal installed and a broker account

## 1. Get the code

```bash
git clone https://github.com/<your-username>/orvo.git
cd orvo
```

(Or simply download/unzip the project folder you received.)

## 2. Backend setup

```bash
cd backend
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows (PowerShell/cmd)

pip install -r requirements.txt
```

On Windows, if you plan to use live MT5 trading, also run:
```bash
pip install MetaTrader5
```

## 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:
- `SECRET_KEY` — generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"
  ```

Everything else has a sensible local-dev default. See inline comments in `.env.example`
for SMTP, news API, and MT5 settings.

## 4. Run the app

```bash
uvicorn app.main:app --reload
```

Visit **http://localhost:8000**. The database (SQLite, `orvo.db`) is created automatically
on first run, along with a default admin account — its temporary password is printed to
the console. Log in and change it from the Profile page immediately.

## 5. Verify

- `http://localhost:8000/api/health` should return `{"status":"ok","app":"ORVO"}`
- `http://localhost:8000/api/docs` shows the interactive Swagger API docs

## Next steps

- [Local Setup Guide](LOCAL_SETUP.md) — day-to-day dev workflow
- [Broker Setup Guide](BROKER_SETUP.md) — connecting MT5
- [Docker Guide](DOCKER_GUIDE.md) — containerized run
- [GitHub Deployment Guide](GITHUB_DEPLOYMENT.md) — pushing to your own repo / hosting
