"""S3 service helpers for upload operations."""

from uuid import uuid4

import boto3

from app.config import Settings


class S3UploadService:
    """Wrapper around S3 upload operations."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    @staticmethod
    def build_object_key(extension: str) -> str:
        """Generate a unique key under the uploads prefix."""
        cleaned_ext = extension.lower().lstrip(".")
        return f"uploads/{uuid4()}.{cleaned_ext}"

    def upload_bytes(self, data: bytes, extension: str, content_type: str) -> str:
        """Upload a payload to S3 and return its object key."""
        object_key = self.build_object_key(extension)
        self._client.put_object(
            Bucket=self._settings.s3_bucket_name,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        return object_key

