# Local Setup Guide

## Running for local development

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`--reload` restarts the server automatically when you edit backend code. The frontend
is plain HTML/CSS/JS served directly by FastAPI (`app/main.py` mounts `/assets` and
serves `*.html` files from `frontend/`), so editing any `.html`/`.js`/`.css` file just
needs a browser refresh — no build step.

## Database

Default: SQLite file at `backend/orvo.db`. Nothing to install. To inspect it:

```bash
sqlite3 backend/orvo.db ".tables"
```

To switch to PostgreSQL, install it locally (or use the bundled Docker service — see
`docs/DOCKER_GUIDE.md`), then set in `.env`:

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/orvo
```

Restart the app — tables are created automatically via SQLAlchemy on startup (no manual
migration step needed for a fresh database).

## Creating your first account

1. Go to `http://localhost:8000/signup.html`
2. Fill in name/email/password (min 8 chars, 1 uppercase, 1 digit)
3. You're logged in immediately and redirected to the dashboard

## Admin access

A default admin account is auto-created on first run — check your terminal output for
its email and one-time password. To promote another existing user to admin, either:

```bash
sqlite3 backend/orvo.db "UPDATE users SET role='admin' WHERE email='you@example.com';"
```

or connect via `psql` if using PostgreSQL.

## Connecting live market data

The AI engine and price ticker use Binance's **public** REST API — no key required, no
signup required. It works immediately as long as your machine has internet access and
isn't in a region where Binance is blocked. If Binance is unreachable in your region,
swap the base URL in `.env` (`BINANCE_REST_URL`) for a Binance mirror, or point
`backend/app/broker/binance_client.py` at an alternative exchange's public API using the
same function signatures.

## Running tests / sanity checks

There's no heavyweight test suite bundled, but you can quickly sanity-check the AI engine
and risk calculations with:

```bash
cd backend
python -c "
from app.ai import technical_analysis as ta, signal_engine
import asyncio
from app.broker import binance_client

async def run():
    candles = await binance_client.get_klines('BTCUSDT', '1h', 200)
    df = ta.candles_to_df(candles)
    result = signal_engine.analyze(df, 'BTCUSDT', '1h')
    print(result['recommendation'], result['confidence'], result['explanation'][:120])

asyncio.run(run())
"
```

(Requires internet access to reach Binance.)

## Common local dev gotchas

- **CORS errors in the browser console**: make sure `ALLOWED_ORIGINS` in `.env` includes
  whatever origin you're loading the app from (`http://localhost:8000` by default).
- **401 errors after leaving the tab open for a while**: your JWT expired
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60). Just log in again.
- **MT5 connect always fails on macOS/Linux**: expected — see `docs/BROKER_SETUP.md`.
