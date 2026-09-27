import io
import uuid

from minio import Minio

from core.config import settings

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


async def upload_file(file, prefix):
    extension = file.filename.rsplit(".", 1)[-1].lower()
    file_name = f"{prefix}-{uuid.uuid4().hex}.{extension}"
    data = await file.read()
    minio_client.put_object(
        settings.MINIO_BUCKET,
        file_name,
        io.BytesIO(data),
        len(data),
        content_type=file.content_type,
    )
    return f"http://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{file_name}"
