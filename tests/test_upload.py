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
