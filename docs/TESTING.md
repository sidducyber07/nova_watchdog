# Nova Watchdog - Rapid Test Guide

Goal: validate end-to-end in under 5 minutes after `docker compose up --build`.

Prerequisites
- Docker Desktop installed and running
- Docker Compose started (`docker compose up --build`)
- API available at `http://localhost:8000`

Quick steps

1. Seed the database (run inside the `api` container or from host with `DATABASE_URL` pointing to Postgres):

```bash
# from repo root
# run inside container: docker compose exec api python backend/scripts/seed_db.py
# or from host if you have Python and DATABASE_URL configured
python backend/scripts/seed_db.py
```

Expected output:
- "Seeded sample user, monitors, and integrations."
- It will print sample monitor IDs.

2. (Optional) Create a monitor via API & register user

```bash
python backend/scripts/create_monitor_via_api.py
```

Expected: 201 Created response for monitor creation.

3. Test a notification channel (uses DB integration entries seeded earlier):

```bash
python backend/scripts/test_notification.py
```

Expected: prints integration tested and result (True/False). If placeholders are used, result may be False.

4. Enqueue a run_monitor task (use sample monitor id from seeding output):

```bash
python backend/scripts/enqueue_run.py <monitor_id>
```

Expected: API returns `{"status":"enqueued","monitor_id":"..."}` and Celery worker logs show task received. The worker will run Playwright, save snapshot to `./data/snapshots/`, and insert a `snapshots` DB row.

5. Verify results
- Check snapshots in Postgres: `SELECT * FROM snapshots ORDER BY run_at DESC LIMIT 5;`
- Check AI summaries: `SELECT * FROM ai_summaries ORDER BY created_at DESC LIMIT 5;`
- Check alerts: `SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;`
- Check snapshots on disk: `ls data/snapshots` (in project root or container at `/data/snapshots`)

Notes and troubleshooting
- If Playwright fails in the worker, ensure the worker image installed browsers (`python -m playwright install`). The `worker.Dockerfile` includes browser install.
- If tasks don't appear, check Flower at http://localhost:5555 and Celery worker logs: `docker compose logs -f worker`.

Sample data
- Seed script creates `test@example.com` user and two monitors (example.com and example.org).
- Sample integrations include a placeholder webhook and telegram entry.

Sample AI rules (examples to add later)
- "Alert me only if pricing changes" — match when selector or text contains 'price' or currency symbols and importance_score > 0.5
- "Ignore footer updates" — exclude changes under CSS selector footer, site-footer
- "Detect policy changes" — look for keywords: 'privacy policy', 'terms', 'cookie policy'

Next steps (to automate soon)
- Upload snapshots to MinIO and store object URLs in `snapshots.assets`
- Add Integration UI in frontend to manage webhooks, telegram, email, slack
- Add natural language AI rules parser and evaluator

