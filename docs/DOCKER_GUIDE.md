# Docker Guide

## Prerequisites
- Docker Desktop (or Docker Engine + Compose plugin on Linux)

## Run it

```bash
cd backend
cp .env.example .env
# edit SECRET_KEY at minimum

cd ../docker
docker compose up --build
```

Visit **http://localhost:8000**.

The container mounts a named volume (`orvo_sqlite_data`) over `/app/backend`, so your
SQLite database persists across `docker compose down` / `up` cycles.

## Using PostgreSQL instead of SQLite

Edit `docker/docker-compose.yml` and uncomment the `postgres` service block and the
`depends_on`/`environment` lines under the `orvo` service. Then:

```bash
docker compose up --build
```

The app will connect to the bundled Postgres container automatically and create tables
on first boot.

## Stopping / cleaning up

```bash
docker compose down          # stop containers, keep volumes (data preserved)
docker compose down -v       # stop and delete volumes (data wiped)
```

## Rebuilding after code changes

```bash
docker compose up --build
```

## Viewing logs

```bash
docker compose logs -f orvo
```

## Notes on MT5 inside Docker

The official `MetaTrader5` Python package requires a running MT5 terminal on Windows —
it cannot run inside a Linux container. If you need live MT5 trading, run the backend
directly on a Windows host (see `docs/INSTALLATION.md`) rather than in Docker, or run
MT5 on a separate Windows machine/VPS and swap in a broker with a real REST API (OANDA,
etc.) for the containerized deployment.
