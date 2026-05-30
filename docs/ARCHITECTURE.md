# Nova Watchdog - Architecture Overview

This document outlines the high-level architecture for Nova Watchdog — a personal, self-hosted website monitoring platform designed to be modular, scalable, and AI-enhanced.

Components
- Frontend: Next.js + TailwindCSS application providing the dashboard, admin UI, and live updates via WebSockets.
- Backend API: FastAPI (Python) providing REST API, WebSocket endpoints, authentication, RBAC, and orchestration.
- Worker System: Distributed workers that execute monitoring tasks using Playwright, capture screenshots, extract DOM/text, and compute diffs. Implemented with Celery (Redis broker) or RQ as a lightweight alternative.
- Scheduler: APScheduler for single-node or Celery Beat for distributed scheduling of jobs.
- Change Detection Engine: Pluggable modules for HTML diffing, DOM-aware diffs, screenshot visual diffs (OpenCV), OCR (Tesseract), and AI semantic comparison.
- AI Service: Optional local LLM (Ollama) or OpenAI integration to generate summaries, scoring, and rule parsing.
- Storage: PostgreSQL for relational data; Redis for caching, rate-limiting, and job queue broker; Object storage (MinIO or S3) for snapshots and screenshots.
- Notifications: Integrations with Telegram, Discord, Email, Slack, webhooks.
- Reverse Proxy: Nginx for TLS termination, routing, and static asset caching.
- Observability: Prometheus metrics and Grafana dashboards; Sentry for error monitoring.

Data Flow
1. User creates a monitor via the dashboard (frontend -> backend REST API).
2. Backend persists monitor config in PostgreSQL and schedules monitoring jobs.
3. Scheduler dispatches jobs to workers via Celery/Redis.
4. Worker runs Playwright to load the page, apply automation (login/cookies), and capture HTML + screenshot + assets.
5. Change Detection Engine compares current snapshot with last accepted snapshot using configured modes.
6. If change is detected and matches user rules, backend records snapshot, stores assets, and triggers notifications.
7. AI Service generates summaries and importance scoring asynchronously; results stored in DB and attached to alerts.
8. Frontend receives live updates via WebSocket and shows change timeline, screenshots, and AI summaries.

Scalability
- Stateless API servers behind a load balancer for horizontal scaling.
- Worker pool autoscaling for throughput; workers are stateless and read tasks from Redis queues.
- Object storage (S3/MinIO) for scalable snapshot storage; use lifecycle rules to prune old snapshots.
- Partitioning monitors across worker pools by region or resource usage (lightweight vs heavy JS pages).

Security
- JWT-based auth with rotating refresh tokens; optional 2FA.
- Secrets stored encrypted (Vault or local encrypted file store).
- Rate limiting per-user and per-IP using Redis.
- Audit logs for critical actions and system events.

Deployment
- Docker Compose for single-host self-hosting.
- Kubernetes manifests for production-grade deployments.

This architecture balances feature richness and personal hosting constraints: basic mode runs on a single VPS using Docker Compose; advanced production requires distributed workers and S3-compatible storage.
