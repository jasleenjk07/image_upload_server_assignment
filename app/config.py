"""Configuration module for environment settings."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket_name: str


def get_settings() -> Settings:
    """Return application settings from process environment."""
    return Settings(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        aws_region=os.getenv("AWS_REGION", ""),
        s3_bucket_name=os.getenv("S3_BUCKET_NAME", ""),
    )

