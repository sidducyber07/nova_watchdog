import asyncio
import json
import uuid
from .celery_app import app
from .workers.playwright_runner import run_check
from .detectors import html_changed, text_changed, visual_diff
from .db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import datetime
from . import notifications
from .storage import get_storage
from .ai_provider import generate_summary
from .rules_engine import evaluate_rules
from .storage import get_storage
from .core.config import MINIO_BUCKET_HTML, MINIO_BUCKET_IMAGES


def _run_sync(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


async def _fetch_previous_snapshot(session: AsyncSession, monitor_id: str):
    q = await session.execute("SELECT id, html, text_content, screenshot_path FROM snapshots WHERE monitor_id = :m ORDER BY run_at DESC LIMIT 1", {"m": monitor_id})
    row = q.fetchone()
    if not row:
        return None
    return {"id": row[0], "html": row[1], "text": row[2], "screenshot_path": row[3]}


async def _insert_snapshot(session: AsyncSession, monitor_id: str, data: dict, diff_summary: dict | None = None):
    sql = """
    INSERT INTO snapshots (id, monitor_id, run_at, status, html, text_content, screenshot_path, assets, metrics, diff_summary, created_at)
    VALUES (:id, :monitor_id, :run_at, :status, :html, :text_content, :screenshot_path, :assets, :metrics, :diff_summary, :created_at)
    """
    await session.execute(sql, {
        "id": data["snapshot_id"],
        "monitor_id": monitor_id,
        "run_at": datetime.datetime.utcnow(),
        "status": "success",
        "html": Path(data["html_path"]).read_text(encoding="utf-8"),
        "text_content": data.get("text"),
        "screenshot_path": data.get("screenshot_path"),
        "assets": json.dumps(data.get("assets", {})),
        "metrics": json.dumps(data.get("metrics", {})),
        "diff_summary": json.dumps(diff_summary or {}),
        "created_at": datetime.datetime.utcnow(),
    })


async def _create_alert(session: AsyncSession, monitor_id: str, snapshot_id: str, severity: str, reason: str):
    sql = """
    INSERT INTO alerts (id, monitor_id, snapshot_id, severity, reason, delivered, deliveries, created_at)
    VALUES (:id, :monitor_id, :snapshot_id, :severity, :reason, false, '[]', :created_at)
    RETURNING id
    """
    alert_id = str(uuid.uuid4())
    await session.execute(sql, {
        "id": alert_id,
        "monitor_id": monitor_id,
        "snapshot_id": snapshot_id,
        "severity": severity,
        "reason": reason,
        "created_at": datetime.datetime.utcnow(),
    })
    return alert_id


async def _fetch_applicable_rules(session: AsyncSession, monitor_id: str):
    q = await session.execute(
        "SELECT id, monitor_id, name, rule_text FROM ai_rules WHERE is_active = true AND (monitor_id = :m OR monitor_id IS NULL)",
        {"m": monitor_id},
    )
    rows = q.fetchall()
    return [models.AIRule(id=row[0], monitor_id=row[1], name=row[2], rule_text=row[3]) for row in rows]


@app.task(name="run_monitor", bind=True)
def run_monitor(self, monitor_id: str):
    """Run a monitoring job lifecycle:
    - Fetch monitor config
    - Capture snapshot via Playwright
    - Compare with previous snapshot using detectors
    - Persist snapshot
    - Create alert if change detected
    - Enqueue AI summary and notifications
    """
    try:
        # fetch monitor config from DB
        async def _run():
            async with AsyncSessionLocal() as session:
                q = await session.execute("SELECT id, url, selector, config FROM monitors WHERE id = :m", {"m": monitor_id})
                row = q.fetchone()
                if not row:
                    raise ValueError("Monitor not found")
                url = row[1]
                selector = row[2]
                config = row[3] or {}

            # capture snapshot
            snapshot = await run_check(url, selector)
            storage = get_storage()
            assets = []
            raw_html = Path(snapshot["html_path"]).read_text(encoding="utf-8")
            cleaned_html = storage.clean_html(raw_html)

            # upload HTML snapshots
            raw_html_key = f"html/raw/{snapshot['snapshot_id']}.html"
            cleaned_html_key = f"html/clean/{snapshot['snapshot_id']}.html"
            assets.append(storage.upload_bytes(MINIO_BUCKET_HTML, raw_html_key, raw_html.encode("utf-8"), "text/html"))
            assets.append(storage.upload_bytes(MINIO_BUCKET_HTML, cleaned_html_key, cleaned_html.encode("utf-8"), "text/html"))

            # upload screenshots
            if snapshot.get("screenshot_path"):
                screenshot_key = f"images/full/{snapshot['snapshot_id']}.png"
                assets.append(storage.upload_file(MINIO_BUCKET_IMAGES, screenshot_key, snapshot["screenshot_path"], "image/png"))

            if snapshot.get("element_path"):
                element_key = f"images/element/{snapshot['snapshot_id']}.png"
                assets.append(storage.upload_file(MINIO_BUCKET_IMAGES, element_key, snapshot["element_path"], "image/png"))

            snapshot["assets"] = assets

            # save snapshot and compare
            async with AsyncSessionLocal() as session:
                prev = await _fetch_previous_snapshot(session, monitor_id)
                # run detectors
                html_res = html_changed(prev["html"] if prev else None, raw_html)
                text_res = text_changed(prev["text"] if prev else None, snapshot.get("text", ""))
                visual_res = {"changed": False}
                if prev and prev.get("screenshot_path") and snapshot.get("screenshot_path"):
                    try:
                        visual_res = visual_diff(prev.get("screenshot_path"), snapshot.get("screenshot_path"))
                    except Exception:
                        visual_res = {"changed": False}

                # run AI summary before rule evaluation
                ai_res = await generate_summary(cleaned_html[:4000] or raw_html[:4000], max_tokens=400)
                ai_summary_id = str(uuid.uuid4())
                ai_summary = ai_res.get("summary", "")
                ai_score = float(ai_res.get("importance_score") or 0.0)
                raw_ai = ai_res.get("raw") or {}
                await session.execute(
                    "INSERT INTO ai_summaries (id, snapshot_id, summary, importance_score, categories, raw_response, created_at) VALUES (:id, :snapshot_id, :summary, :score, :cats, :raw, :created_at)",
                    {
                        "id": ai_summary_id,
                        "snapshot_id": snapshot["snapshot_id"],
                        "summary": ai_summary,
                        "score": ai_score,
                        "cats": json.dumps([]),
                        "raw": json.dumps(raw_ai),
                        "created_at": datetime.datetime.utcnow(),
                    },
                )

                diff_summary = {
                    "html": html_res,
                    "text": text_res,
                    "visual": visual_res,
                    "ai_score": ai_score,
                    "rule_check": {},
                }

                rules = await _fetch_applicable_rules(session, monitor_id)
                allowed, rule_reason = evaluate_rules(rules, selector, raw_html, cleaned_html, snapshot.get("text", ""), ai_score, diff_summary)
                diff_summary["rule_check"] = {"allowed": allowed, "reason": rule_reason}

                await _insert_snapshot(session, monitor_id, snapshot, diff_summary)

                change_detected = html_res.get("changed") or text_res.get("changed") or visual_res.get("changed")
                if allowed and change_detected:
                    severity = "warning" if text_res.get("ratio", 0) < 0.5 else "critical"
                    reason = json.dumps({"html": html_res, "text": text_res, "visual": visual_res, "rules": rule_reason})
                    alert_id = await _create_alert(session, monitor_id, snapshot["snapshot_id"], severity, reason)
                    app.send_task("send_notifications", args=[alert_id], queue="notifications")

            return {"status": "completed", "snapshot_id": snapshot["snapshot_id"], "rule_allowed": allowed, "rule_reason": rule_reason}

        return _run_sync(_run())
    except Exception as exc:
        raise exc


@app.task(name="ai_process")
def ai_process(snapshot_id: str):
    """Generate AI summary for a snapshot and persist it."""
    try:
        async def _do():
            from .ai_provider import generate_summary

            async with AsyncSessionLocal() as session:
                q = await session.execute("SELECT id, html, text_content FROM snapshots WHERE id = :s", {"s": snapshot_id})
                row = q.fetchone()
                if not row:
                    return None
                html = row[1] or ""
                text = row[2] or ""
                content = (text or html)[:4000]
                ai_res = await generate_summary(content, max_tokens=400)
                summary = ai_res.get("summary") or ""
                score = float(ai_res.get("importance_score") or 0.0)
                raw = ai_res.get("raw") or {}
                summary_id = str(uuid.uuid4())
                await session.execute("INSERT INTO ai_summaries (id, snapshot_id, summary, importance_score, categories, raw_response, created_at) VALUES (:id, :snapshot_id, :summary, :score, :cats, :raw, :created_at)", {
                    "id": summary_id,
                    "snapshot_id": snapshot_id,
                    "summary": summary,
                    "score": score,
                    "cats": json.dumps([]),
                    "raw": json.dumps(raw),
                    "created_at": datetime.datetime.utcnow()
                })
                await session.commit()
                return True

        return _run_sync(_do())
    except Exception:
        return None


@app.task(name="send_notifications")
def send_notifications(alert_id: str):
    """Fetch alert & monitor info and send notifications using configured integrations."""
    try:
        async def _do():
            async with AsyncSessionLocal() as session:
                q = await session.execute("SELECT a.id, a.reason, m.id as monitor_id, m.name FROM alerts a JOIN monitors m ON m.id = a.monitor_id WHERE a.id = :id", {"id": alert_id})
                row = q.fetchone()
                if not row:
                    return False
                reason = row[1]
                monitor_name = row[3]

                # fetch integrations for the monitor owner (simple: all integrations)
                q2 = await session.execute("SELECT id, type, config FROM integrations WHERE is_active = true")
                integrations = q2.fetchall()

                deliveries = []
                for integ in integrations:
                    integ_id, integ_type, integ_cfg = integ[0], integ[1], integ[2]
                    ok = False
                    try:
                        if integ_type == "telegram":
                            ok = await notifications.send_telegram(integ_cfg, f"Change detected on {monitor_name}: {reason}")
                        elif integ_type == "discord":
                            ok = await notifications.send_discord(integ_cfg, f"Change detected on {monitor_name}: {reason}")
                        elif integ_type == "slack":
                            ok = await notifications.send_slack(integ_cfg, f"Change detected on {monitor_name}: {reason}")
                        elif integ_type == "email":
                            # expect config to include recipient and SMTP settings
                            ok = await notifications.send_email(integ_cfg, f"Change detected: {monitor_name}", reason)
                        elif integ_type == "webhook":
                            ok = await notifications.send_webhook(integ_cfg, {"monitor": monitor_name, "reason": reason})
                    except Exception:
                        ok = False
                    deliveries.append({"integration_id": integ_id, "ok": ok, "ts": datetime.datetime.utcnow().isoformat()})

                # update alert deliveries
                await session.execute("UPDATE alerts SET delivered = true, deliveries = :d WHERE id = :id", {"d": json.dumps(deliveries), "id": alert_id})
                await session.commit()
                return True

        return _run_sync(_do())
    except Exception:
        return False


@app.task(name="dead_letter_handler")
def dead_letter_handler(task_name: str, args, kwargs, error: str):
    # simple logging sink for failed tasks; in production move to durable store for inspection
    payload = {"task": task_name, "args": args, "kwargs": kwargs, "error": error}
    Path("/var/log/nova_watchdog_dead_letter").mkdir(parents=True, exist_ok=True)
    Path(f"/var/log/nova_watchdog_dead_letter/{task_name}_{int(datetime.datetime.utcnow().timestamp())}.json").write_text(json.dumps(payload))
    return True
