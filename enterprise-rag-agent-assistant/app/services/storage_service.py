from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import re
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.utils.logger import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class StorageResult:
    filename: str
    storage_provider: str
    storage_path: str
    object_key: str | None
    public_url: str | None


class BaseStorageService(ABC):
    @abstractmethod
    async def save_file(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StorageResult:
        """
        Save file bytes and return storage metadata.
        """

    async def save_upload_file(self, file: UploadFile) -> StorageResult:
        content = await file.read()
        return await self.save_file(
            filename=file.filename or "",
            content=content,
            content_type=file.content_type,
        )


class LocalStorageService(BaseStorageService):
    def __init__(self, upload_dir: str | None = None) -> None:
        self.upload_dir = Path(upload_dir or settings.upload_dir)

    async def save_upload_file(self, file: UploadFile) -> StorageResult:
        """
        Backward-compatible wrapper around the bytes-based save API.
        """
        content = await file.read()
        return await self.save_file(
            filename=file.filename or "",
            content=content,
            content_type=file.content_type,
        )

    async def save_file(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StorageResult:
        original_filename = sanitize_filename(filename)

        if not original_filename:
            raise ValueError("filename cannot be empty.")

        if not content:
            raise ValueError("Uploaded file content is empty.")

        self.upload_dir.mkdir(parents=True, exist_ok=True)

        saved_filename = f"{uuid4().hex}_{original_filename}"
        saved_path = self.upload_dir / saved_filename

        try:
            saved_path.write_bytes(content)

        except Exception as exc:
            logger.exception(
                "Failed to save upload file | provider=local | filename=%s | upload_dir=%s",
                original_filename,
                self.upload_dir,
            )
            raise RuntimeError(f"Failed to save upload file: {original_filename}") from exc

        logger.info(
            "Upload file saved | provider=local | filename=%s | storage_path=%s",
            original_filename,
            saved_path,
        )

        return StorageResult(
            filename=original_filename,
            storage_provider="local",
            storage_path=str(saved_path),
            object_key=saved_filename,
            public_url=None,
        )


class COSStorageService(BaseStorageService):
    def __init__(self) -> None:
        self.bucket = settings.cos_bucket
        self.region = settings.cos_region
        self.prefix = normalize_prefix(settings.cos_prefix)

        missing_fields = [
            name
            for name, value in {
                "COS_SECRET_ID": settings.cos_secret_id,
                "COS_SECRET_KEY": settings.cos_secret_key,
                "COS_BUCKET": self.bucket,
                "COS_REGION": self.region,
            }.items()
            if not value.strip()
        ]

        if missing_fields:
            raise ValueError(
                "Missing required COS settings: " + ", ".join(missing_fields)
            )

        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError as exc:
            raise RuntimeError(
                "cos-python-sdk-v5 is required when STORAGE_PROVIDER=cos."
            ) from exc

        config = CosConfig(
            Region=self.region,
            SecretId=settings.cos_secret_id,
            SecretKey=settings.cos_secret_key,
        )
        self.client = CosS3Client(config)

    async def save_upload_file(self, file: UploadFile) -> StorageResult:
        """
        Backward-compatible wrapper around the bytes-based save API.
        """
        content = await file.read()
        return await self.save_file(
            filename=file.filename or "",
            content=content,
            content_type=file.content_type,
        )

    async def save_file(
        self,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> StorageResult:
        original_filename = sanitize_filename(filename)

        if not original_filename:
            raise ValueError("filename cannot be empty.")

        if not content:
            raise ValueError("Uploaded file content is empty.")

        object_key = f"{self.prefix}{uuid4().hex}_{original_filename}"

        try:
            put_object_kwargs = {
                "Bucket": self.bucket,
                "Body": content,
                "Key": object_key,
            }

            if content_type:
                put_object_kwargs["ContentType"] = content_type

            self.client.put_object(**put_object_kwargs)

        except Exception as exc:
            logger.exception(
                "Failed to save upload file to COS | bucket=%s | region=%s | object_key=%s",
                self.bucket,
                self.region,
                object_key,
            )
            raise RuntimeError(
                f"Failed to save upload file to COS: {original_filename}"
            ) from exc

        logger.info(
            "Upload file saved to COS | bucket=%s | region=%s | object_key=%s",
            self.bucket,
            self.region,
            object_key,
        )

        return StorageResult(
            filename=original_filename,
            storage_provider="cos",
            storage_path=f"cos://{self.bucket}/{object_key}",
            object_key=object_key,
            public_url=None,
        )


def get_storage_service() -> BaseStorageService:
    provider = settings.storage_provider.lower().strip()

    if provider == "local":
        return LocalStorageService()

    if provider == "cos":
        return COSStorageService()

    raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = safe_name.replace("/", "_").replace("\\", "_")
    safe_name = re.sub(r"[\x00-\x1f\x7f]+", "_", safe_name)
    safe_name = re.sub(r"\s+", "_", safe_name)

    if safe_name in {"", ".", ".."}:
        raise ValueError("filename cannot be empty or unsafe.")

    return safe_name


def normalize_prefix(prefix: str) -> str:
    safe_prefix = prefix.strip().lstrip("/")

    if safe_prefix and not safe_prefix.endswith("/"):
        safe_prefix += "/"

    return safe_prefix
