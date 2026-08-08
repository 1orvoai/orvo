# ORVO — AI Trading Platform

ORVO is a self-hosted trading dashboard that combines:
- A real, rule-based technical/AI analysis engine (trend, structure, BOS/CHOCH, Fair Value Gaps, order blocks, supply/demand, volatility, sessions) running on live Binance market data
- Real risk management (position sizing, daily loss limits, drawdown caps, trailing stops, breakeven)
- Real broker execution via MetaTrader 5 (Windows-only — see limitation below)
- Full JWT authentication, admin panel, and a dark/light themed dashboard

## ⚠️ Read this first — what's real vs. what needs your own setup

Everything in this project is real, working code — nothing is mocked or faked. But some
features depend on external services that only *you* can provide credentials/licenses for:

| Feature | Status |
|---|---|
| Auth (signup/login/reset/JWT) | ✅ Fully working out of the box |
| Dashboard, risk engine, lot calculator | ✅ Fully working out of the box |
| AI analysis (trend/SMC/FVG/order blocks) | ✅ Fully working — live crypto data via Binance's free public API |
| TradingView charts | ✅ Fully working — official free embeddable widget |
| MT5 broker connection & live trading | ⚠️ Real integration, but **Windows-only**, and requires a MetaTrader 5 terminal installed and logged into your broker. This is a limitation of the official `MetaTrader5` Python package itself — not something ORVO can work around. |
| Password reset emails | ⚠️ Real SMTP sending — requires you to add your own SMTP credentials (e.g. a Gmail App Password) to `.env`. Without it, reset links are printed to the server console instead of emailed. |
| Economic calendar / high-impact news | ⚠️ Real integration — requires a free API key from finnhub.io or financialmodelingprep.com. Without a key it clearly reports "not configured" rather than showing fake events. |
| Forex/Gold/Index AI analysis | ⚠️ The AI engine currently analyzes symbols available on Binance (crypto). Charts for forex/gold/indices work via TradingView, but running the AI engine on them requires wiring in a forex/gold data provider (e.g. OANDA, Polygon, Twelve Data) — the engine itself (`backend/app/ai/`) is provider-agnostic and easy to point at a new data source. |

No legitimate trading system can guarantee profits. ORVO's AI engine gives you a transparent,
explainable confidence score from real price-action rules — treat it as a decision-support tool.

## Quick start (local)

See [`docs/LOCAL_SETUP.md`](docs/LOCAL_SETUP.md) for full details. Short version:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit SECRET_KEY at minimum
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the ORVO splash screen loads, then the landing page.
On first run, a default admin account is created and its temporary password is printed
to the console — log in and change it immediately from the Profile page.

## Project structure

```
orvo/
├── backend/                 FastAPI application
│   ├── app/
│   │   ├── main.py          App entrypoint, middleware, static file serving
│   │   ├── config.py        All configuration (from environment variables)
│   │   ├── database.py      SQLAlchemy engine/session
│   │   ├── models.py        ORM models (users, trades, risk settings, broker connections...)
│   │   ├── schemas.py       Pydantic request/response schemas
│   │   ├── security.py      Password hashing, JWT, credential encryption
│   │   ├── deps.py          Auth dependencies (get_current_user, get_current_admin)
│   │   ├── email_service.py Real SMTP email sending
│   │   ├── routers/         API endpoints (auth, trading, dashboard, admin, etc.)
│   │   ├── ai/               AI/technical-analysis engine
│   │   ├── broker/          MT5 connector + Binance market-data client
│   │   └── risk/            Risk management calculations
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 Static HTML/CSS/JS (Tailwind via CDN)
│   ├── index.html, login.html, signup.html, dashboard.html, trading.html, ...
│   └── assets/{css,js}/
├── docker/                   Dockerfile + docker-compose.yml
└── docs/                     Full documentation set
```

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Local Setup Guide](docs/LOCAL_SETUP.md)
- [GitHub Deployment Guide](docs/GITHUB_DEPLOYMENT.md)
- [Docker Guide](docs/DOCKER_GUIDE.md)
- [Broker Setup Guide](docs/BROKER_SETUP.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## Security

- Passwords hashed with bcrypt (passlib)
- JWT bearer authentication on every protected route
- Broker credentials encrypted at rest (Fernet, key derived from `SECRET_KEY`)
- Rate limiting (slowapi) on all endpoints
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS in production)
- CORS restricted to configured origins
- SQL injection protected via SQLAlchemy's parameterized queries (no raw string SQL anywhere)
- `.env` is git-ignored — no secrets are ever committed

## License

Provided as-is for your own deployment. Trading involves substantial risk of loss —
review `docs/TROUBLESHOOTING.md` and the broker/legal notes before connecting a live account.
