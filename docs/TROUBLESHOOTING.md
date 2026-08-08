# Troubleshooting Guide

## Server won't start

**`ModuleNotFoundError: No module named 'fastapi'` (or similar)**
You haven't activated your virtual environment or installed dependencies.
```bash
cd backend
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**`sqlalchemy.exc.OperationalError` on startup**
Usually means `DATABASE_URL` points somewhere unreachable (e.g. a Postgres host that
isn't running). Switch back to the SQLite default in `.env` to confirm the app itself
is fine, then fix your Postgres connection separately.

## Login/signup issues

**"Incorrect email or password" but you're sure it's right**
Emails are stored lowercase. Make sure you're not accidentally including trailing
whitespace when copy-pasting.

**401 errors on every page after being logged in for a while**
Your JWT expired (`ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`, default 60 minutes).
This is expected — just log in again. Increase the value in `.env` if you want longer
sessions during development.

**Password reset email never arrives**
Check your server console — if `SMTP_HOST`/`SMTP_USER`/`SMTP_PASSWORD` aren't set in
`.env`, ORVO prints the reset link to the console instead of emailing it (clearly
logged as `[ORVO][email:NOT SENT - SMTP not configured]`). Configure real SMTP
credentials to send real emails — see `.env.example` for a Gmail App Password example.

## Broker connection issues

**"MetaTrader5 package only runs on Windows"**
Correct — this is a real limitation of the official package, not a bug. See
`docs/BROKER_SETUP.md` for your options (run on Windows, or use OANDA/Alpaca instead).

**"MT5 login failed: (-6, 'Terminal: Authorization failed')" (or similar tuple error)**
This is the exact error MT5 itself returned — check your login number, password, and
server name match exactly what's shown inside the MT5 terminal's login window
(case-sensitive server names are a common culprit).

**Broker shows "connected" but orders fail with "Symbol not found"**
Your broker's symbol naming may differ (e.g. `EURUSD.a` instead of `EURUSD`). Check the
"Market Watch" panel inside your MT5 terminal for the exact symbol name it uses.

## Market data / AI analysis issues

**"Could not fetch market data" on the Trading or Dashboard page**
The backend calls Binance's public API directly — this needs outbound internet access
from wherever the backend is running, and Binance must not be blocked in that region/
network. If it's blocked, set a different `BINANCE_REST_URL` in `.env` pointing at an
accessible mirror, or swap the client for another exchange's public API.

**AI analysis says "Not enough candle history"**
The engine needs at least 55 candles to compute trend/structure reliably — this can
happen right after Binance lists a brand-new pair. Try a longer-established symbol or
a shorter timeframe.

## Docker issues

**`docker compose up` fails with a port conflict**
Something else is already using port 8000. Change the host port in
`docker/docker-compose.yml`, e.g. `"8001:8000"`, then visit `http://localhost:8001`.

**Database resets every time you restart the container**
You likely ran `docker compose down -v`, which deletes volumes. Use `docker compose down`
(without `-v`) to preserve data between restarts.

## Admin panel

**Can't access `/admin.html` — redirected to dashboard**
Your account isn't an admin. Either use the auto-created admin account (its email/
temp-password were printed to the console on first run), or promote your account
directly in the database — see `docs/LOCAL_SETUP.md` → "Admin access".

## Still stuck?

Check `http://localhost:8000/api/docs` for the live, interactive API reference — every
endpoint, its expected request body, and its response schema is documented there
automatically from the FastAPI code, so you can test any endpoint directly and see the
exact error the backend returns.
