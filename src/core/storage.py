from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from src.core.config import get_settings

settings = get_settings()

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


class StorageManager:
    """MinIO storage manager."""
    
    def __init__(self):
        self.client = minio_client
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            raise Exception(f"Failed to create bucket: {e}")
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload file to MinIO."""
        try:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                metadata=metadata or {},
            )
            
            return f"{self.bucket_name}/{object_name}"
            
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")
    
    async def download_file(self, object_name: str) -> bytes:
        """Download file from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response.read()
        except S3Error as e:
            raise Exception(f"Failed to download file: {e}")
    
    async def delete_file(self, object_name: str) -> None:
        """Delete file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"Failed to delete file: {e}")
    
    async def file_exists(self, object_name: str) -> bool:
        """Check if file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    async def get_file_url(self, object_name: str, expires_in_seconds: int = 3600) -> str:
        """Get presigned URL for file access."""
        try:
            return self.client.presigned_get_object(
                self.bucket_name, object_name, expires_in_seconds
            )
        except S3Error as e:
            raise Exception(f"Failed to generate presigned URL: {e}")


storage_manager = StorageManager()

