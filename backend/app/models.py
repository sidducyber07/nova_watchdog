import datetime
import sqlalchemy as sa
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = sa.Column(sa.String, primary_key=True)
    email = sa.Column(sa.String, unique=True, index=True, nullable=False)
    hashed_password = sa.Column(sa.String, nullable=False)
    full_name = sa.Column(sa.String)
    is_active = sa.Column(sa.Boolean, default=True)
    is_admin = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)


class Monitor(Base):
    __tablename__ = "monitors"
    id = sa.Column(sa.String, primary_key=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = sa.Column(sa.String, nullable=False)
    url = sa.Column(sa.String, nullable=False)
    selector = sa.Column(sa.String)
    mode = sa.Column(sa.String, default="rendered")
    frequency_seconds = sa.Column(sa.Integer, default=3600)
    config = sa.Column(sa.JSON, default={})
    last_status = sa.Column(sa.String)
    is_paused = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Integration(Base):
    __tablename__ = "integrations"
    id = sa.Column(sa.String, primary_key=True)
    user_id = sa.Column(sa.String, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    type = sa.Column(sa.String, nullable=False)
    name = sa.Column(sa.String, nullable=False)
    config = sa.Column(sa.JSON, default={})
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AIRule(Base):
    __tablename__ = "ai_rules"
    id = sa.Column(sa.String, primary_key=True)
    monitor_id = sa.Column(sa.String, sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=True)
    name = sa.Column(sa.String, nullable=False)
    rule_text = sa.Column(sa.String, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Snapshot(Base):
    __tablename__ = "snapshots"
    id = sa.Column(sa.String, primary_key=True)
    monitor_id = sa.Column(sa.String, sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False)
    run_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
    status = sa.Column(sa.String, nullable=False)
    html = sa.Column(sa.Text)
    text_content = sa.Column(sa.Text)
    dom = sa.Column(sa.JSON, default={})
    screenshot_path = sa.Column(sa.String)
    assets = sa.Column(sa.JSON, default=[])
    metrics = sa.Column(sa.JSON, default={})
    diff_summary = sa.Column(sa.JSON, default={})
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)


class AISummary(Base):
    __tablename__ = "ai_summaries"
    id = sa.Column(sa.String, primary_key=True)
    snapshot_id = sa.Column(sa.String, sa.ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    summary = sa.Column(sa.Text)
    importance_score = sa.Column(sa.Float)
    categories = sa.Column(sa.JSON, default=[])
    raw_response = sa.Column(sa.JSON, default={})
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = sa.Column(sa.String, primary_key=True)
    monitor_id = sa.Column(sa.String, sa.ForeignKey("monitors.id", ondelete="CASCADE"), nullable=False)
    snapshot_id = sa.Column(sa.String, sa.ForeignKey("snapshots.id", ondelete="SET NULL"), nullable=True)
    severity = sa.Column(sa.String, default="info")
    reason = sa.Column(sa.Text)
    delivered = sa.Column(sa.Boolean, default=False)
    deliveries = sa.Column(sa.JSON, default=[])
    ai_summary_id = sa.Column(sa.String, sa.ForeignKey("ai_summaries.id", ondelete="SET NULL"), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), default=datetime.datetime.utcnow)
