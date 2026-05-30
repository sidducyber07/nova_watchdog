from pydantic import BaseModel, EmailStr
from typing import Optional, Any, List


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]

    class Config:
        orm_mode = True


class MonitorCreate(BaseModel):
    name: str
    url: str
    selector: Optional[str]
    frequency_seconds: Optional[int] = 3600
    mode: Optional[str] = "rendered"
    config: Optional[Any]


class MonitorUpdate(BaseModel):
    name: Optional[str]
    url: Optional[str]
    selector: Optional[str]
    frequency_seconds: Optional[int]
    mode: Optional[str]
    config: Optional[Any]


class MonitorOut(BaseModel):
    id: str
    name: str
    url: str
    selector: Optional[str]
    mode: str
    frequency_seconds: int
    last_status: Optional[str]
    is_paused: bool

    class Config:
        orm_mode = True


class IntegrationBase(BaseModel):
    type: str
    name: str
    config: Optional[Any]
    is_active: Optional[bool] = True


class IntegrationCreate(IntegrationBase):
    pass


class IntegrationUpdate(BaseModel):
    name: Optional[str]
    config: Optional[Any]
    is_active: Optional[bool]


class IntegrationOut(IntegrationBase):
    id: str

    class Config:
        orm_mode = True


class AIRuleBase(BaseModel):
    name: str
    rule_text: str
    monitor_id: Optional[str]
    is_active: Optional[bool] = True


class AIRuleCreate(AIRuleBase):
    pass


class AIRuleUpdate(BaseModel):
    name: Optional[str]
    rule_text: Optional[str]
    monitor_id: Optional[str]
    is_active: Optional[bool]


class AIRuleOut(AIRuleBase):
    id: str

    class Config:
        orm_mode = True


class SnapshotOut(BaseModel):
    id: str
    monitor_id: str
    run_at: Optional[str]
    status: str
    screenshot_path: Optional[str]
    assets: Optional[Any]
    diff_summary: Optional[Any]

    class Config:
        orm_mode = True


class AlertOut(BaseModel):
    id: str
    monitor_id: str
    snapshot_id: Optional[str]
    severity: str
    reason: Optional[str]
    delivered: bool
    deliveries: Optional[Any]
    created_at: Optional[str]

    class Config:
        orm_mode = True


class AISummaryOut(BaseModel):
    id: str
    snapshot_id: str
    summary: Optional[str]
    importance_score: Optional[float]
    categories: Optional[Any]
    created_at: Optional[str]

    class Config:
        orm_mode = True
