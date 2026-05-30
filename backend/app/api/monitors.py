from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import models, schemas
import uuid
from ..celery_app import app as celery_app

router = APIRouter(prefix="/monitors", tags=["monitors"])


@router.get("/", response_model=list[schemas.MonitorOut])
async def list_monitors(db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Monitor))
    rows = q.scalars().all()
    return rows


@router.post("/", response_model=schemas.MonitorOut, status_code=201)
async def create_monitor(m_in: schemas.MonitorCreate, db: AsyncSession = Depends(get_db)):
    monitor = models.Monitor(id=str(uuid.uuid4()), name=m_in.name, url=m_in.url, selector=m_in.selector, frequency_seconds=m_in.frequency_seconds or 3600, mode=m_in.mode or "rendered", config=m_in.config)
    async with db.begin():
        db.add(monitor)
    await db.commit()
    return monitor


@router.get("/{monitor_id}", response_model=schemas.MonitorOut)
async def get_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Monitor).where(models.Monitor.id == monitor_id))
    monitor = q.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.patch("/{monitor_id}", response_model=schemas.MonitorOut)
async def update_monitor(monitor_id: str, payload: schemas.MonitorUpdate, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Monitor).where(models.Monitor.id == monitor_id))
    monitor = q.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    if payload.name is not None:
        monitor.name = payload.name
    if payload.url is not None:
        monitor.url = payload.url
    if payload.selector is not None:
        monitor.selector = payload.selector
    if payload.frequency_seconds is not None:
        monitor.frequency_seconds = payload.frequency_seconds
    if payload.mode is not None:
        monitor.mode = payload.mode
    if payload.config is not None:
        monitor.config = payload.config
    async with db.begin():
        db.add(monitor)
    await db.commit()
    return monitor


@router.delete("/{monitor_id}")
async def delete_monitor(monitor_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Monitor).where(models.Monitor.id == monitor_id))
    monitor = q.scalar_one_or_none()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    await db.delete(monitor)
    await db.commit()
    return {"status": "deleted", "monitor_id": monitor_id}


@router.post('/{monitor_id}/run')
async def trigger_run(monitor_id: str):
    """Trigger an immediate run for a monitor (enqueues Celery task)."""
    # send to monitoring queue
    celery_app.send_task('run_monitor', args=[monitor_id], queue='monitoring')
    return {"status": "enqueued", "monitor_id": monitor_id}
