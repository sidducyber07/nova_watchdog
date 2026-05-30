import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minio123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() in ("true", "1", "yes")
MINIO_BUCKET_HTML = os.getenv("MINIO_BUCKET_HTML", "snapshots-html")
MINIO_BUCKET_IMAGES = os.getenv("MINIO_BUCKET_IMAGES", "snapshots-images")
MINIO_BUCKET_EXPORTS = os.getenv("MINIO_BUCKET_EXPORTS", "exports")
MINIO_BUCKETS = [MINIO_BUCKET_HTML, MINIO_BUCKET_IMAGES, MINIO_BUCKET_EXPORTS]
MINIO_DEFAULT_EXPIRES_SECONDS = int(os.getenv("MINIO_DEFAULT_EXPIRES_SECONDS", "3600"))
MINIO_RETENTION_DAYS = int(os.getenv("MINIO_RETENTION_DAYS", "90"))
