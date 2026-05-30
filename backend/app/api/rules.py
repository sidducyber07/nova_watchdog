import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_db
from .. import models, schemas

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("/", response_model=list[schemas.AIRuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.AIRule))
    return q.scalars().all()


@router.post("/", response_model=schemas.AIRuleOut, status_code=201)
async def create_rule(payload: schemas.AIRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = models.AIRule(
        id=str(uuid.uuid4()),
        monitor_id=payload.monitor_id,
        name=payload.name,
        rule_text=payload.rule_text,
        is_active=payload.is_active,
    )
    async with db.begin():
        db.add(rule)
    await db.commit()
    return rule


@router.get("/{rule_id}", response_model=schemas.AIRuleOut)
async def get_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.AIRule).where(models.AIRule.id == rule_id))
    rule = q.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=schemas.AIRuleOut)
async def update_rule(rule_id: str, payload: schemas.AIRuleUpdate, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.AIRule).where(models.AIRule.id == rule_id))
    rule = q.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    if payload.name is not None:
        rule.name = payload.name
    if payload.rule_text is not None:
        rule.rule_text = payload.rule_text
    if payload.monitor_id is not None:
        rule.monitor_id = payload.monitor_id
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    async with db.begin():
        db.add(rule)
    await db.commit()
    return rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str, db: AsyncSession = Depends(get_db)):
    q = await db.execute(models.sa.select(models.AIRule).where(models.AIRule.id == rule_id))
    rule = q.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"status": "deleted", "id": rule_id}
