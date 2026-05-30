from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/snapshots", tags=["snapshots"])

@router.get("/", response_model=list[schemas.SnapshotOut])
async def list_snapshots(monitor_id: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    stmt = models.sa.select(models.Snapshot).order_by(models.Snapshot.created_at.desc())
    if monitor_id:
        stmt = stmt.where(models.Snapshot.monitor_id == monitor_id)
    q = await db.execute(stmt)
    return q.scalars().all()


@router.get("/{snapshot_id}", response_model=schemas.SnapshotOut)
async def get_snapshot(snapshot_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.Snapshot).where(models.Snapshot.id == snapshot_id))
    snapshot = q.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot
