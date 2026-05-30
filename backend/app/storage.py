import time
from datetime import datetime, timedelta
import io
import re
from typing import Any
from minio import Minio
from minio.error import S3Error
from .core.config import (
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_SECURE,
    MINIO_BUCKET_HTML,
    MINIO_BUCKET_IMAGES,
    MINIO_BUCKET_EXPORTS,
    MINIO_DEFAULT_EXPIRES_SECONDS,
    MINIO_RETENTION_DAYS,
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class MinioStorage:
    def __init__(self):
        self.client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )
        self.buckets = [MINIO_BUCKET_HTML, MINIO_BUCKET_IMAGES, MINIO_BUCKET_EXPORTS]
        self._ensure_buckets()

    def _retry(self, func, *args, **kwargs):
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except S3Error as exc:
                last_exc = exc
                if attempt == MAX_RETRIES:
                    raise
                time.sleep(RETRY_DELAY_SECONDS * attempt)
        raise last_exc

    def _ensure_buckets(self):
        for bucket_name in self.buckets:
            exists = self._retry(self.client.bucket_exists, bucket_name)
            if not exists:
                self._retry(self.client.make_bucket, bucket_name)
                self.set_retention_policy(bucket_name, MINIO_RETENTION_DAYS)

    def set_retention_policy(self, bucket_name: str, days: int):
        """Create a lifecycle policy for auto-deletion after `days`."""
        if days <= 0:
            return
        rule = f"<LifecycleConfiguration>\n  <Rule>\n    <ID>expire-{days}-days</ID>\n    <Status>Enabled</Status>\n    <Filter><Prefix></Prefix></Filter>\n    <Expiration><Days>{days}</Days></Expiration>\n  </Rule>\n</LifecycleConfiguration>"
        try:
            self._retry(self.client.set_bucket_lifecycle, bucket_name, rule)
        except Exception:
            # not critical if lifecycle config isn't supported by provider
            pass

    def upload_file(self, bucket_name: str, object_name: str, file_path: str, content_type: str) -> dict:
        """Upload a local file to a bucket and return metadata."""
        stat = None
        def _upload():
            self.client.fput_object(bucket_name, object_name, file_path, content_type=content_type)
        self._retry(_upload)
        stat = self.client.stat_object(bucket_name, object_name)
        return self._asset_metadata(bucket_name, object_name, stat, content_type)

    def upload_bytes(self, bucket_name: str, object_name: str, data: bytes, content_type: str) -> dict:
        """Upload raw bytes to a bucket."""
        def _upload():
            self.client.put_object(bucket_name, object_name, io.BytesIO(data), len(data), content_type=content_type)
        self._retry(_upload)
        stat = self.client.stat_object(bucket_name, object_name)
        return self._asset_metadata(bucket_name, object_name, stat, content_type)

    def get_object(self, bucket_name: str, object_name: str) -> bytes:
        def _get():
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        return self._retry(_get)

    def clean_html(self, html: str) -> str:
        """Produce a cleaned HTML snapshot suitable for comparison and storage."""
        html = re.sub(r"(?is)<script.*?>.*?</script>", "", html)
        html = re.sub(r"(?is)<style.*?>.*?</style>", "", html)
        html = re.sub(r"(?s)<!--.*?-->", "", html)
        html = re.sub(r"\s+", " ", html).strip()
        return html

    def get_presigned_url(self, bucket_name: str, object_name: str, expires: int = MINIO_DEFAULT_EXPIRES_SECONDS) -> str:
        return self.client.presigned_get_object(bucket_name, object_name, expires=timedelta(seconds=expires))

    def _asset_metadata(self, bucket_name: str, object_name: str, stat: Any, content_type: str) -> dict:
        return {
            "bucket": bucket_name,
            "key": object_name,
            "url": self.get_presigned_url(bucket_name, object_name),
            "content_type": content_type,
            "size": stat.size,
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
        }


_storage_instance: MinioStorage | None = None


def get_storage() -> MinioStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MinioStorage()
    return _storage_instance
