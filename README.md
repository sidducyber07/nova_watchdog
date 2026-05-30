# 🔍 Nova Watchdog

> **A powerful, self-hosted website monitoring and alerting platform** with AI-driven change detection, multi-channel notifications, and an elegant dashboard.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-13.4+-000000?style=flat-square&logo=next.js)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Web Monitoring** | Capture full-page and element-specific snapshots with Playwright |
| 🔄 **Change Detection** | Multi-mode comparison (HTML, text, visual) with intelligent diffing |
| 🤖 **AI Summaries** | OpenAI or Ollama-powered change summaries with importance scoring |
| 📏 **Smart Rules Engine** | Natural-language rule matching for alert gating and noise reduction |
| 🔔 **Multi-Channel Alerts** | Telegram, Discord, Slack, Email (SMTP), and custom webhooks |
| 📊 **Rich Dashboard** | Monitor management, rule authoring, integration setup, and alert history |
| ⚡ **Async Pipeline** | Celery + Redis queue system with dead-letter handling |
| 💾 **Object Storage** | MinIO S3-compatible storage for snapshots and exports |
| 🔐 **JWT Auth** | Secure API with user registration and token-based access |
| 🐳 **Container Ready** | Docker Compose for one-command deployment |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     NOVA WATCHDOG PLATFORM                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐        ┌──────────────┐                        │
│  │   Frontend   │        │  Dashboard   │                        │
│  │  (Next.js)   │◄──────►│   (React)    │                        │
│  └──────┬───────┘        └──────┬───────┘                        │
│         │                        │                               │
│         └────────┬───────────────┘                               │
│                  │                                               │
│         ┌────────▼───────┐                                       │
│         │   FastAPI      │                                       │
│         │   REST API     │                                       │
│         └────────┬───────┘                                       │
│                  │                                               │
│    ┌─────────────┼──────────────┐                               │
│    │             │              │                               │
│ ┌──▼──┐   ┌─────▼─────┐   ┌────▼────┐                           │
│ │ Auth│   │ Monitors  │   │ Rules   │                           │
│ │     │   │ Snapshots │   │ Alerts  │                           │
│ └─────┘   │ Integr.   │   │         │                           │
│           └───────────┘   └─────────┘                           │
│                  │                                               │
│    ┌─────────────┼──────────────┐                               │
│    │             │              │                               │
│ ┌──▼──┐   ┌─────▼─────┐   ┌────▼────┐                           │
│ │Redis│   │ PostgreSQL│   │ MinIO   │                           │
│ │Queue│   │    DB     │   │ Storage │                           │
│ └─────┘   └───────────┘   └─────────┘                           │
│                  │                                               │
│    ┌─────────────▼──────────────┐                               │
│    │  Celery Worker Pipeline    │                               │
│    │  (Playwright, AI, Notify)  │                               │
│    └────────────────────────────┘                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

### 1️⃣ Docker Compose (Recommended)

```bash
# Clone and navigate
git clone <repo>
cd nova_watchdog

# Start the full stack
docker compose up --build

# Wait for services to initialize (~30s)
# Then open:
# - Dashboard:   http://localhost:3000
# - API Docs:    http://localhost:8000/docs
# - MinIO:       http://localhost:9000
# - Flower:      http://localhost:5555
```

**Default credentials:**
- MinIO: `minio` / `minio123`
- PostgreSQL: `nova` / `nova`
- Dashboard: No auth on localhost (add JWT in production)

### 2️⃣ Local Development

#### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install --with-deps

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API available at:** `http://localhost:8000/docs`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

**Dashboard available at:** `http://localhost:3000`

---

## 📋 Implementation Guide

### Core Concepts

#### 1. **Monitors**
Create monitors to track website changes. Each monitor:
- Specifies a target URL and optional CSS selector
- Defines capture mode (rendered or static)
- Sets check frequency in seconds
- Stores metadata and configuration

```bash
# Example: Create a monitor
curl -X POST http://localhost:8000/monitors/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Homepage Tracker",
    "url": "https://example.com",
    "selector": "#main-content",
    "frequency_seconds": 3600,
    "mode": "rendered"
  }'
```

#### 2. **Snapshots**
Each monitor run captures:
- **Full HTML**: Raw and cleaned versions (script/style/comment removed)
- **Screenshots**: Full-page and element-specific PNG images
- **Text Content**: Extracted plain text for comparison
- **Metrics**: Performance and size metadata

#### 3. **Change Detection**
Three detection modes analyze differences:
- **HTML Changes**: Structure comparison via normalized difflib
- **Text Changes**: Content similarity ratio
- **Visual Changes**: Image diffing using OpenCV (edge detection)

#### 4. **AI Summaries**
Snapshots are processed by:
- **OpenAI API** (default): High-quality natural language summaries
- **Ollama** (fallback): Local LLM for privacy-focused setups
- Produces: Summary text + importance score (0-1)

#### 5. **Rules Engine**
Natural-language rule matching controls alerts:
- **Ignore rules**: Skip alerts matching conditions
- **Alert-only rules**: Alert only when conditions match
- **Conditions**: Price, security, footer, cookie, importance, selector

```bash
# Example rules
"Alert only when price changes"
"Ignore footer-only changes"
"Notify if importance > 0.7"
"Alert only if selector '.product-list' changed"
```

#### 6. **Integrations**
Configure multi-channel notifications:

| Integration | Config Fields | Use Case |
|-------------|---------------|----------|
| **Telegram** | `bot_token`, `chat_id` | Instant mobile alerts |
| **Discord** | `webhook_url` | Team notifications |
| **Slack** | `webhook_url` | Workspace integration |
| **Email** | `host`, `port`, `username`, `password`, `sender`, `recipient` | Email delivery |
| **Webhook** | `url`, `headers` (optional) | Custom endpoints |

#### 7. **Alert Workflow**
```
Monitor Run
    ↓
Capture Snapshot
    ↓
Detect Changes (HTML/Text/Visual)
    ↓
Generate AI Summary
    ↓
Evaluate Rules
    ↓
Create Alert (if allowed)
    ↓
Send Notifications (all active integrations)
    ↓
Track Delivery Status
```

---

## 🎯 API Reference

### Authentication
```bash
# Register user
POST /auth/register
{
  "email": "user@example.com",
  "password": "secure-password",
  "full_name": "John Doe"
}

# Login to get token
POST /auth/login
{
  "email": "user@example.com",
  "password": "secure-password"
}
# Returns: { "access_token": "...", "token_type": "bearer" }

# Get current user
GET /auth/me
Headers: { "Authorization": "Bearer <token>" }
```

### Monitors
```bash
# List all monitors
GET /monitors/

# Create monitor
POST /monitors/
{
  "name": "string",
  "url": "string",
  "selector": "string (optional)",
  "frequency_seconds": integer,
  "mode": "rendered | static"
}

# Get monitor details
GET /monitors/{monitor_id}

# Update monitor
PATCH /monitors/{monitor_id}

# Delete monitor
DELETE /monitors/{monitor_id}

# Trigger immediate run
POST /monitors/{monitor_id}/run
```

### Integrations
```bash
# List integrations
GET /integrations/

# Create integration
POST /integrations/
{
  "type": "telegram|discord|slack|email|webhook",
  "name": "string",
  "config": { ...type-specific fields },
  "is_active": boolean
}

# Test integration
POST /integrations/{integration_id}/test

# Check health
GET /integrations/{integration_id}/health

# Update integration
PATCH /integrations/{integration_id}

# Delete integration
DELETE /integrations/{integration_id}
```

### Rules
```bash
# List rules
GET /rules/

# Create rule
POST /rules/
{
  "name": "string",
  "rule_text": "string",
  "monitor_id": "string (optional, null = global)",
  "is_active": boolean
}

# Update rule
PATCH /rules/{rule_id}
{
  "name": "string",
  "rule_text": "string",
  "is_active": boolean
}

# Delete rule
DELETE /rules/{rule_id}
```

### Alerts & Snapshots
```bash
# List alerts
GET /alerts/?monitor_id=<optional>

# Get alert details
GET /alerts/{alert_id}

# List snapshots
GET /snapshots/?monitor_id=<optional>

# Get snapshot details
GET /snapshots/{snapshot_id}
```

### Health Check
```bash
GET /healthz
# Returns: { "status": "ok" }
```

---

## 🎨 Dashboard Pages

| Page | Features |
|------|----------|
| **Dashboard** | Quick overview, monitor list, navigation hub |
| **Monitors** | Create, list, trigger runs, view status |
| **Integrations** | CRUD for notification channels, test & health checks |
| **AI Rules** | Create/edit/delete rules, enable/disable globally |
| **Alerts** | Browse all alerts with severity and delivery status |
| **Snapshots** | Review captured snapshots and diff summaries |

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nova_watchdog

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=your-super-secret-key-change-in-prod
JWT_ALGORITHM=HS256

# MinIO Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123
MINIO_SECURE=false
MINIO_BUCKET_HTML=snapshots-html
MINIO_BUCKET_IMAGES=snapshots-images
MINIO_BUCKET_EXPORTS=exports
MINIO_RETENTION_DAYS=90

# AI Provider
OPENAI_API_KEY=sk-...
OLLAMA_ENDPOINT=http://localhost:11434
```

### Celery Queues

Workers process tasks via dedicated queues:
- `monitoring`: Main monitor execution
- `screenshots`: Screenshot processing
- `ai`: AI summary generation
- `notifications`: Alert delivery
- `dead_letter`: Failed task recovery

---

## 🐳 Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| **frontend** | 3000 | Next.js dashboard |
| **api** | 8000 | FastAPI REST backend |
| **worker** | — | Celery task processor |
| **beat** | — | Celery scheduler |
| **flower** | 5555 | Celery monitoring UI |
| **redis** | 6379 | Message broker & cache |
| **postgres** | 5432 | Primary database |
| **minio** | 9000 | S3 object storage |

---

## 📊 Monitoring & Debugging

### Flower Dashboard
Monitor Celery tasks in real-time:
```bash
http://localhost:5555
```

### API Documentation
Interactive Swagger UI:
```bash
http://localhost:8000/docs
```

### MinIO Console
Manage stored snapshots:
```bash
http://localhost:9000
```

---

## 🔐 Security Best Practices

1. **Change JWT Secret** in production
2. **Use HTTPS** for all external connections
3. **Rotate credentials** regularly
4. **Enable database backups** for PostgreSQL
5. **Restrict API access** with firewall rules
6. **Validate webhooks** with HMAC signatures
7. **Store secrets** in environment variables only
8. **Enable MINIO_SECURE** for production MinIO

---

## 📦 Tech Stack

```
Frontend:         Next.js 13 + React 18 + Tailwind CSS + SWR
Backend:          FastAPI + SQLAlchemy + Pydantic
Database:         PostgreSQL 15 + AsyncPG
Cache & Queue:    Redis 7 + Celery 5
Storage:          MinIO (S3-compatible)
Monitoring:       Playwright + OpenCV + Pillow
AI:               OpenAI API + Ollama
Notifications:    aiosmtplib + httpx
Deployment:       Docker Compose
```

---

## 🚦 Usage Examples

### Example 1: Monitor a Product Page

```bash
# 1. Create monitor
curl -X POST http://localhost:8000/monitors/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Pricing",
    "url": "https://shop.example.com/product/123",
    "selector": ".price",
    "frequency_seconds": 3600,
    "mode": "rendered"
  }'

# 2. Create price-change rule
curl -X POST http://localhost:8000/rules/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Price Alert",
    "rule_text": "Alert only when price changes",
    "monitor_id": "<monitor_id>",
    "is_active": true
  }'

# 3. Create Telegram integration
curl -X POST http://localhost:8000/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "telegram",
    "name": "Price Alerts",
    "config": {
      "bot_token": "123:ABC...",
      "chat_id": "999"
    },
    "is_active": true
  }'

# 4. Trigger run
curl -X POST http://localhost:8000/monitors/<monitor_id>/run
```

### Example 2: Security Monitoring

```bash
# Monitor login page for suspicious changes
curl -X POST http://localhost:8000/monitors/ \
  -d '{
    "name": "Login Page Security",
    "url": "https://app.example.com/login",
    "frequency_seconds": 1800,
    "mode": "rendered"
  }'

# Alert on security keywords
curl -X POST http://localhost:8000/rules/ \
  -d '{
    "name": "Security Alert",
    "rule_text": "Alert if security keywords detected",
    "is_active": true
  }'
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/awesome-feature`)
3. Commit changes (`git commit -m 'Add awesome feature'`)
4. Push to branch (`git push origin feature/awesome-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 💡 Tips & Tricks

- **Optimize snapshots**: Use CSS selectors to capture only relevant areas
- **Reduce false alerts**: Create ignore rules for known dynamic content
- **Batch operations**: Combine multiple monitors for better resource utilization
- **Export data**: Use webhooks to sync alerts to external systems
- **Test integrations**: Always run the `test` endpoint before going live

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **API not responding** | Check if `docker compose` services are running: `docker compose ps` |
| **No snapshots captured** | Ensure Playwright is installed: `python -m playwright install --with-deps` |
| **Alerts not sending** | Verify integration config with test endpoint; check firewall/proxy |
| **High memory usage** | Reduce `MINIO_RETENTION_DAYS` or delete old snapshots manually |
| **Database connection error** | Verify `DATABASE_URL` env var and PostgreSQL is running |

---

## 📞 Support

- 📖 [Full Documentation](https://github.com/your-repo/docs)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Discussions](https://github.com/your-repo/discussions)

---

<div align="center">

**Made with ❤️ for the open-source community**

[⬆ back to top](#-nova-watchdog)

</div>
