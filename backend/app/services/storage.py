import os
from abc import ABC, abstractmethod
from app.core.config import settings


class StorageService(ABC):
    @abstractmethod
    def save_file(self, file_bytes: bytes, filename: str, user_id: int) -> str:
        """Save file and return a unique key or file path."""
        pass

    @abstractmethod
    def delete_file(self, file_key: str) -> bool:
        """Delete file by key or path."""
        pass

    @abstractmethod
    def get_file_bytes(self, file_key: str) -> bytes:
        """Get file content as bytes."""
        pass


class LocalStorageService(StorageService):
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def _get_path(self, file_key: str) -> str:
        # Prevent path traversal attacks
        safe_key = os.path.basename(file_key)
        return os.path.join(self.upload_dir, safe_key)

    def save_file(self, file_bytes: bytes, filename: str, user_id: int) -> str:
        # Create a unique filename prefix to avoid collisions
        import uuid
        unique_id = uuid.uuid4().hex
        safe_filename = f"{user_id}_{unique_id}_{os.path.basename(filename)}"
        filepath = os.path.join(self.upload_dir, safe_filename)
        
        with open(filepath, "wb") as f:
            f.write(file_bytes)
            
        return safe_filename

    def delete_file(self, file_key: str) -> bool:
        filepath = self._get_path(file_key)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except OSError:
                return False
        return False

    def get_file_bytes(self, file_key: str) -> bytes:
        filepath = self._get_path(file_key)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {file_key}")
        with open(filepath, "rb") as f:
            return f.read()


class S3StorageService(StorageService):
    def __init__(self):
        # Initialize boto3 S3 client lazily so that backend starts even if boto3 is not configured
        try:
            import boto3
            self.s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        except ImportError:
            self.s3 = None
        self.bucket = settings.AWS_BUCKET_NAME

    def _check_client(self):
        if not self.s3:
            raise ImportError("boto3 is not installed or configured. Run pip install boto3.")

    def save_file(self, file_bytes: bytes, filename: str, user_id: int) -> str:
        self._check_client()
        import uuid
        unique_id = uuid.uuid4().hex
        s3_key = f"uploads/{user_id}/{unique_id}_{filename}"
        
        from io import BytesIO
        self.s3.upload_fileobj(BytesIO(file_bytes), self.bucket, s3_key)
        return s3_key

    def delete_file(self, file_key: str) -> bool:
        self._check_client()
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=file_key)
            return True
        except Exception:
            return False

    def get_file_bytes(self, file_key: str) -> bytes:
        self._check_client()
        from io import BytesIO
        try:
            out = BytesIO()
            self.s3.download_fileobj(self.bucket, file_key, out)
            out.seek(0)
            return out.read()
        except Exception as e:
            raise FileNotFoundError(f"Failed to fetch S3 file: {e}")


def get_storage_service() -> StorageService:
    if settings.USE_S3:
        return S3StorageService()
    return LocalStorageService()
