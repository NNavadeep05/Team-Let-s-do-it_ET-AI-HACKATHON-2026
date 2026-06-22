import io
from datetime import timedelta
from minio import Minio
from app.config import settings


class StorageService:
    def __init__(self):
        # MinIO is compatible with standard S3 API, we use the minio SDK client.
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        """Upload a file to MinIO."""
        data_stream = io.BytesIO(data)
        self.client.put_object(
            self.bucket,
            key,
            data_stream,
            length=len(data),
            content_type=content_type
        )

    async def get(self, key: str) -> bytes:
        """Download a file from MinIO."""
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def presign(self, key: str, expires_minutes: int = 5) -> str:
        """Generate a presigned GET URL for an object (default TTL 5 minutes)."""
        url = self.client.presigned_get_object(
            self.bucket,
            key,
            expires=timedelta(minutes=expires_minutes)
        )
        return url


storage_service = StorageService()


async def get_storage():
    """Dependency for getting storage service."""
    yield storage_service
