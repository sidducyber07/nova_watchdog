# Database Schema (PostgreSQL)

This schema targets core entities needed for monitoring, snapshots, alerts, users, and AI summaries. Use `UUID` primary keys and `JSONB` for flexible fields.

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  full_name TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  is_admin BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Organizations / optional
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Projects (folders/tags)
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  name TEXT NOT NULL,
  color TEXT,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Monitors
CREATE TABLE monitors (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  url TEXT NOT NULL,
  mode TEXT NOT NULL DEFAULT 'rendered', -- rendered, raw, pdf
  selector TEXT, -- CSS selector or XPath
  frequency_seconds INTEGER NOT NULL DEFAULT 3600,
  config JSONB DEFAULT '{}'::jsonb, -- advanced settings: headers, cookies, viewport, auth, ignore_rules
  last_run_at TIMESTAMP WITH TIME ZONE,
  last_status TEXT,
  is_paused BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_monitors_user ON monitors(user_id);
CREATE INDEX idx_monitors_url ON monitors(url);

-- Snapshots (one per successful check)
CREATE TABLE snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  monitor_id UUID REFERENCES monitors(id) ON DELETE CASCADE,
  run_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  status TEXT NOT NULL, -- success, failed
  html TEXT,
  text_content TEXT,
  dom JSONB,
  screenshot_path TEXT,
  assets JSONB, -- list of uploaded MinIO asset metadata
  metrics JSONB, -- timings, size
  diff_summary JSONB, -- structured diff output (counts, changed selectors, hashes)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Example assets JSON entry:
-- [
--   {
--     "bucket": "snapshots-html",
--     "key": "html/raw/<snapshot_id>.html",
--     "url": "https://minio.example.com/snapshots-html/html/raw/<snapshot_id>.html?X-Amz-...",
--     "content_type": "text/html",
--     "size": 12345,
--     "uploaded_at": "2026-05-30T12:00:00Z"
--   },
--   {
--     "bucket": "snapshots-images",
--     "key": "images/full/<snapshot_id>.png",
--     "url": "https://...",
--     "content_type": "image/png",
--     "size": 34567,
--     "uploaded_at": "2026-05-30T12:00:02Z"
--   }
-- ]

CREATE INDEX idx_snapshots_monitor_runat ON snapshots(monitor_id, run_at DESC);

-- Alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  monitor_id UUID REFERENCES monitors(id) ON DELETE CASCADE,
  snapshot_id UUID REFERENCES snapshots(id) ON DELETE SET NULL,
  severity TEXT DEFAULT 'info', -- info, warning, critical
  reason TEXT,
  delivered BOOLEAN DEFAULT FALSE,
  deliveries JSONB DEFAULT '[]'::jsonb, -- records of notifications
  ai_summary_id UUID REFERENCES ai_summaries(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- AI Summaries
CREATE TABLE ai_summaries (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  snapshot_id UUID REFERENCES snapshots(id) ON DELETE CASCADE,
  summary TEXT,
  importance_score REAL,
  categories JSONB,
  raw_response JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Notifications / Integrations
CREATE TABLE integrations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  type TEXT NOT NULL, -- telegram, discord, email, webhook
  name TEXT,
  config JSONB,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Audit logs
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  action TEXT,
  target JSONB,
  meta JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Worker / queue tracking
CREATE TABLE workers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT,
  last_heartbeat TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Optional: key-value store for locks and dedupe (but Redis recommended)
CREATE TABLE kv_store (
  key TEXT PRIMARY KEY,
  value JSONB,
  ttl TIMESTAMP WITH TIME ZONE
);

-- Notes
-- Use JSONB for flexible fields. Add GIN indexes where needed for querying JSON content.

