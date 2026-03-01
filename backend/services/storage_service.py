import asyncio
from abc import ABC, abstractmethod
from functools import lru_cache


class StorageService(ABC):

    @abstractmethod
    async def generate_presigned_put_url(self, key: str, content_type: str, expires_in: int = 900) -> str:
        raise NotImplementedError

    @abstractmethod
    async def generate_presigned_get_url(self, key: str, expires_in: int = 1800, internal: bool = False) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upload_file(self, local_path: str, key: str) -> bool:
        raise NotImplementedError


class S3StorageService(StorageService):
    """S3-compatible 實作，支援 MinIO / Cloudflare R2 / AWS S3 / Backblaze B2"""

    def __init__(self, access_key_id: str, secret_access_key: str, bucket_name: str, endpoint_url: str, public_url: str = "") -> None:
        import boto3
        self._bucket = bucket_name
        # 內部操作（delete / upload）使用 Docker 內部 endpoint
        self._client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            endpoint_url=endpoint_url,
            region_name="auto",
        )
        # presigned URL 生成使用公開 endpoint
        # 簽章的 Host 必須與瀏覽器請求的 Host 一致，不可事後替換 hostname
        presigned_endpoint = public_url.rstrip("/") if public_url else endpoint_url
        if presigned_endpoint != endpoint_url:
            self._presigned_client = boto3.client(
                "s3",
                aws_access_key_id=access_key_id,
                aws_secret_access_key=secret_access_key,
                endpoint_url=presigned_endpoint,
                region_name="auto",
            )
        else:
            self._presigned_client = self._client

    async def generate_presigned_put_url(self, key: str, content_type: str, expires_in: int = 900) -> str:
        return self._presigned_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires_in,
        )

    async def generate_presigned_get_url(self, key: str, expires_in: int = 1800, internal: bool = False) -> str:
        """生成 presigned GET URL。
        internal=True：使用內部 endpoint（供後端 httpx/FFmpeg 存取 MinIO）。
        internal=False（預設）：使用公開 endpoint（供瀏覽器存取）。
        """
        client = self._client if internal else self._presigned_client
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    async def delete_object(self, key: str) -> bool:
        try:
            await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False

    async def upload_file(self, local_path: str, key: str) -> bool:
        import os
        try:
            await asyncio.to_thread(self._client.upload_file, local_path, self._bucket, key)
            return True
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)


@lru_cache
def get_storage_service() -> StorageService:
    from backend.config import get_settings
    settings = get_settings()
    return S3StorageService(
        access_key_id=settings.s3_access_key_id,
        secret_access_key=settings.s3_secret_access_key,
        bucket_name=settings.s3_bucket_name,
        endpoint_url=settings.s3_endpoint_url,
        public_url=settings.s3_public_url,
    )
