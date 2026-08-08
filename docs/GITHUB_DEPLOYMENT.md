# GitHub & Deployment Guide

## Publishing to GitHub

```bash
cd orvo
git init
git add .
git commit -m "Initial commit: ORVO AI trading platform"
git branch -M main
git remote add origin https://github.com/<your-username>/orvo.git
git push -u origin main
```

`.gitignore` already excludes `backend/.env` and the SQLite database file, so your
secrets and local data are never pushed. Double-check before your first push:

```bash
git status --short | grep -E "\.env$|orvo\.db$"
```
This should print nothing.

## Deploying online

ORVO's backend is a standard FastAPI/Uvicorn app, so it runs on any platform that supports
Python or Docker containers. A few real options:

### Option A — Render / Railway / Fly.io (simplest)
1. Push to GitHub (above).
2. Create a new "Web Service" pointing at your repo, root directory `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all variables from `.env.example` as environment variables in the platform's dashboard
   (never commit real secrets — set them in the platform UI instead).
6. Attach a managed PostgreSQL add-on and set `DATABASE_URL` to its connection string.

### Option B — Your own VPS (DigitalOcean, Hetzner, EC2, etc.)
1. `git clone` your repo on the server.
2. Follow `docs/DOCKER_GUIDE.md` to run via Docker Compose — this is the most reliable
   path since it doesn't depend on the host's Python version.
3. Put nginx or Caddy in front for HTTPS (Caddy can auto-provision Let's Encrypt certs
   with a single line: `your-domain.com { reverse_proxy localhost:8000 }`).

### Option C — Docker on any container host
See `docs/DOCKER_GUIDE.md`. Works on any host that runs Docker (Render, Railway, Fly.io,
Google Cloud Run, AWS ECS, etc.) — just build and push `docker/Dockerfile`.

## Important production checklist

- [ ] Generate a real `SECRET_KEY` (never use the default)
- [ ] Set `ENV=production` and `DEBUG=false`
- [ ] Use PostgreSQL, not SQLite, for anything beyond single-user local testing
- [ ] Set `ALLOWED_ORIGINS` to your real domain only
- [ ] Put the app behind HTTPS (the security headers middleware adds HSTS automatically
      when `ENV=production`, but you still need a TLS certificate — Caddy/nginx/Cloudflare)
- [ ] Configure real SMTP credentials so password resets actually send
- [ ] MT5 live trading only works from a Windows host — if you're hosting ORVO on Linux,
      either run MT5 on a separate Windows VPS ORVO can reach, or switch to a broker with
      a native REST API (e.g. OANDA) for that environment — see `docs/BROKER_SETUP.md`.
