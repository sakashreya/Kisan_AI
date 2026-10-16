import io
import os
import tempfile
import time
from minio import Minio
from .config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

BUCKET = "audio"
_client = None


def client():
    global _client
    if _client is None:
        _client = Minio(MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, secure=False)
        if not _client.bucket_exists(BUCKET):
            _client.make_bucket(BUCKET)
    return _client


def save_audio(data: bytes, phone: str) -> str:
    """Store the voice note in MinIO and also return a local temp path for Whisper."""
    name = f"{phone}/{int(time.time())}.ogg"
    try:
        client().put_object(BUCKET, name, io.BytesIO(data), len(data), content_type="audio/ogg")
    except Exception as e:  # storage is optional for the pipeline to work
        print("MinIO error:", e)
    fd, path = tempfile.mkstemp(suffix=".ogg")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path


def save_temp(data: bytes, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path
