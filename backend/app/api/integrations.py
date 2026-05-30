import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import models, schemas, notifications

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/", response_model=list[schemas.IntegrationOut])
async def list_integrations(db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration))
    return q.scalars().all()


@router.post("/", response_model=schemas.IntegrationOut, status_code=201)
async def create_integration(payload: schemas.IntegrationCreate, db: AsyncSession = Depends(get_db)):
    integration = models.Integration(
        id=str(uuid.uuid4()),
        user_id=None,
        type=payload.type,
        name=payload.name,
        config=payload.config or {},
        is_active=payload.is_active,
    )
    async with db.begin():
        db.add(integration)
    await db.commit()
    return integration


@router.get("/{integration_id}", response_model=schemas.IntegrationOut)
async def get_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration).where(models.Integration.id == integration_id))
    integration = q.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    return integration


@router.patch("/{integration_id}", response_model=schemas.IntegrationOut)
async def update_integration(integration_id: str, payload: schemas.IntegrationUpdate, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration).where(models.Integration.id == integration_id))
    integration = q.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    if payload.name is not None:
        integration.name = payload.name
    if payload.config is not None:
        integration.config = payload.config
    if payload.is_active is not None:
        integration.is_active = payload.is_active
    async with db.begin():
        db.add(integration)
    await db.commit()
    return integration


@router.delete("/{integration_id}")
async def delete_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration).where(models.Integration.id == integration_id))
    integration = q.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    await db.delete(integration)
    await db.commit()
    return {"status": "deleted", "id": integration_id}


@router.post("/{integration_id}/test")
async def test_integration(integration_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration).where(models.Integration.id == integration_id))
    integration = q.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    details = []
    ok = False
    try:
        if integration.type == "telegram":
            ok = await notifications.send_telegram(integration.config, "Nova Watchdog integration test message.")
        elif integration.type == "discord":
            ok = await notifications.send_discord(integration.config, "Nova Watchdog integration test message.")
        elif integration.type == "slack":
            ok = await notifications.send_slack(integration.config, "Nova Watchdog integration test message.")
        elif integration.type == "webhook":
            ok = await notifications.send_webhook(integration.config, {"event": "integration_test", "message": "Nova Watchdog integration test."})
        elif integration.type == "email":
            ok = await notifications.send_email(integration.config, "Nova Watchdog test", "This is a test email from Nova Watchdog.")
        else:
            raise ValueError("Unsupported integration type")
        details.append({"sent": ok})
    except Exception as exc:
        details.append({"error": str(exc)})
        ok = False
    return {"ok": ok, "type": integration.type, "details": details}


@router.get("/{integration_id}/health")
async def integration_health(integration_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Integration).where(models.Integration.id == integration_id))
    integration = q.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    q2 = await db.execute("SELECT id, deliveries, created_at FROM alerts WHERE deliveries IS NOT NULL ORDER BY created_at DESC LIMIT 20")
    rows = q2.fetchall()
    last_success = None
    last_failure = None
    events = []
    for row in rows:
        deliveries = row[1]
        try:
            deliveries = json.loads(deliveries)
        except Exception:
            deliveries = []
        for item in deliveries:
            if item.get("integration_id") == integration_id:
                status = "success" if item.get("ok") else "failure"
                ts = item.get("ts")
                events.append({"status": status, "ts": ts})
                if status == "success" and not last_success:
                    last_success = ts
                if status == "failure" and not last_failure:
                    last_failure = ts
    return {"integration_id": integration_id, "type": integration.type, "last_success": last_success, "last_failure": last_failure, "events": events}
