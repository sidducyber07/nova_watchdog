from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import auth, monitors, integrations, rules, alerts, snapshots
from .db import engine, Base
from .storage import get_storage

app = FastAPI(title="Nova Watchdog API")

# Allow localhost frontend during development
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # create DB tables in dev mode; use migrations in production
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # ensure MinIO storage buckets exist at startup
    get_storage()._ensure_buckets()


app.include_router(auth.router)
app.include_router(monitors.router)
app.include_router(integrations.router)
app.include_router(rules.router)
app.include_router(alerts.router)
app.include_router(snapshots.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
