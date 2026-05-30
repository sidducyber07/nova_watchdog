# Nova Watchdog - Backend

Quickstart (dev):

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
```

2. Run the app:

```bash
uvicorn app.main:app --reload --port 8000
```

Notes:
- By default the app uses SQLite (`DATABASE_URL` env var can point to Postgres). Use Alembic for migrations in production.
- This scaffold includes basic JWT auth and monitor endpoints for initial development.

Docker Compose (dev single-host with workers):

```bash
cp .env.example .env
docker-compose up --build
```

This will start services: `redis`, `postgres`, `minio`, `api`, `worker`, and `flower` (Celery monitoring).

The backend now uploads snapshots and screenshots to MinIO buckets:
- `snapshots-html`
- `snapshots-images`
- `exports`

Quick validation (after services are up):

```bash
# seed DB
docker compose exec api python backend/scripts/seed_db.py
# enqueue test run (use printed monitor id)
docker compose exec api python backend/scripts/enqueue_run.py <monitor_id>
# check worker logs
docker compose logs -f worker
```
