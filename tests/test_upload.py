"""Upload endpoint tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_upload_accepts_supported_extension_and_content_type() -> None:
    response = client.post(
        "/upload",
        files={"file": ("photo.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"filename": "photo.png"}


def test_upload_rejects_file_larger_than_2mb() -> None:
    too_large = b"a" * (2 * 1024 * 1024 + 1)
    response = client.post(
        "/upload",
        files={"file": ("large.png", too_large, "image/png")},
    )

    assert response.status_code == 413
    assert response.json() == {"error": "File exceeds 2 MB size limit."}
