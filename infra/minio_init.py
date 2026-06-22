import os
from minio import Minio
from minio.versioning import VersioningConfig
from minio.commonconfig import ENABLED

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "neuron-iq")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() in ("true", "1")


def init_minio():
    print(f"Initializing MinIO bucket at {MINIO_ENDPOINT}...")
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

    if not client.bucket_exists(MINIO_BUCKET):
        print(f"Creating bucket '{MINIO_BUCKET}'")
        client.make_bucket(MINIO_BUCKET)
    else:
        print(f"Bucket '{MINIO_BUCKET}' already exists.")

    print(f"Enabling versioning on bucket '{MINIO_BUCKET}'")
    client.set_bucket_versioning(MINIO_BUCKET, VersioningConfig(ENABLED))
    print("MinIO initialization complete.")


if __name__ == "__main__":
    init_minio()
