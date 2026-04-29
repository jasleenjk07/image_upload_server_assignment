"""Upload endpoint tests."""

import sys
from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app import main

client = TestClient(main.app)


def test_health_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_missing_file_returns_400() -> None:
    response = client.post("/upload")

    assert response.status_code == 400
    assert response.json() == {"error": "No file uploaded"}


def test_upload_rejects_unsupported_extension() -> None:
    response = client.post(
        "/upload",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json() == {
        "error": "Unsupported file extension. Only JPG, JPEG, and PNG are allowed."
    }


def test_upload_rejects_unsupported_content_type() -> None:
    response = client.post(
        "/upload",
        files={"file": ("image.png", b"fake-image", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json() == {
        "error": "Unsupported content type. Only image/jpeg and image/png are allowed."
    }


def test_upload_accepts_supported_extension_and_content_type(monkeypatch) -> None:
    class MockS3Service:
        def upload_bytes(self, data: bytes, extension: str, content_type: str) -> str:
            assert data == b"fake-image"
            assert extension == "png"
            assert content_type == "image/png"
            return "uploads/test-image.png"

    monkeypatch.setattr(main, "get_s3_service", lambda: MockS3Service())
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(s3_bucket_name="demo-bucket"),
    )

    response = client.post(
        "/upload",
        files={"file": ("photo.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 200
    assert response.json() == {
        "url": "https://demo-bucket.s3.amazonaws.com/uploads/test-image.png",
    }


def test_upload_rejects_file_larger_than_2mb() -> None:
    too_large = b"a" * (2 * 1024 * 1024 + 1)
    response = client.post(
        "/upload",
        files={"file": ("large.png", too_large, "image/png")},
    )

    assert response.status_code == 413
    assert response.json() == {"error": "File exceeds 2 MB size limit."}


def test_upload_s3_failure_returns_500(monkeypatch) -> None:
    class BrokenS3Service:
        def upload_bytes(self, data: bytes, extension: str, content_type: str) -> str:
            raise RuntimeError("boom")

    monkeypatch.setattr(main, "get_s3_service", lambda: BrokenS3Service())

    response = client.post(
        "/upload",
        files={"file": ("photo.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 500
    assert response.json() == {"error": "S3 upload failed."}


def test_upload_missing_aws_credentials_returns_500(monkeypatch) -> None:
    monkeypatch.setattr(
        main,
        "get_s3_service",
        lambda: (_ for _ in ()).throw(ValueError("AWS credentials are missing or invalid.")),
    )

    response = client.post(
        "/upload",
        files={"file": ("photo.png", b"fake-image", "image/png")},
    )
    assert response.status_code == 500
    assert response.json() == {"error": "AWS credentials are missing or invalid."}
