from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/", response_model=list[schemas.AlertOut])
async def list_alerts(monitor_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = models.sa.select(models.Alert).order_by(models.Alert.created_at.desc())
    if monitor_id:
        stmt = stmt.where(models.Alert.monitor_id == monitor_id)
    q = await db.execute(stmt)
    return q.scalars().all()


@router.get("/{alert_id}", response_model=schemas.AlertOut)
async def get_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Alert).where(models.Alert.id == alert_id))
    alert = q.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
