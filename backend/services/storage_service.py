from abc import ABC, abstractmethod
from functools import lru_cache


class StorageService(ABC):

    @abstractmethod
    async def generate_presigned_put_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upload_file(self, local_path: str, key: str) -> bool:
        raise NotImplementedError


class LocalStorageService(StorageService):

    async def generate_presigned_put_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("local 後端不支援 Presigned URL，請改用 /videos/upload 端點")

    async def generate_presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        raise NotImplementedError("local 後端不支援 Presigned URL")

    async def delete_object(self, key: str) -> bool:
        import os
        if os.path.exists(key):
            os.remove(key)
            return True
        return False

    async def upload_file(self, local_path: str, key: str) -> bool:
        raise NotImplementedError("local 後端不支援 upload_file")


class R2StorageService(StorageService):

    def __init__(self, access_key_id: str, secret_access_key: str, bucket_name: str, endpoint_url: str) -> None:
        import boto3
        self._bucket = bucket_name
        self._client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name="auto",
        )

    async def generate_presigned_put_url(self, key: str, content_type: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def delete_object(self, key: str) -> bool:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def upload_file(self, local_path: str, key: str) -> bool:
        import os
        try:
            self._client.upload_file(local_path, self._bucket, key)
            return True
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)


@lru_cache
def get_storage_service() -> StorageService:
    from backend.config import get_settings
    settings = get_settings()
    if settings.storage_backend == "r2":
        return R2StorageService(
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
            endpoint_url=settings.r2_endpoint_url,
        )
    return LocalStorageService()
