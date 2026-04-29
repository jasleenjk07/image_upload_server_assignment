"""FastAPI application entrypoint."""

import os

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.s3_service import S3UploadService

app = FastAPI()
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
BACKEND_PORT = os.getenv("BACKEND_PORT")


@app.get("/health")
def health() -> dict[str, str]:
    """Simple readiness endpoint."""
    return {"status": "ok"}


def error_response(message: str, status_code: int) -> JSONResponse:
    """Return a consistent error payload."""
    return JSONResponse(status_code=status_code, content={"error": message})


def get_s3_service() -> S3UploadService:
    """Create an S3 upload service from environment settings."""
    settings = get_settings()
    if not all(
        [
            settings.aws_access_key_id,
            settings.aws_secret_access_key,
            settings.aws_region,
            settings.s3_bucket_name,
        ]
    ):
        raise ValueError("AWS credentials are missing or invalid.")
    return S3UploadService(settings)


@app.post("/upload")
async def upload_file(file: UploadFile | None = File(default=None)) -> dict[str, str]:
    """Upload endpoint with validation and S3 integration."""
    if file is None:
        return error_response("No file uploaded", 400)

    filename = (file.filename or "").strip()
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return error_response("Unsupported file extension. Only JPG, JPEG, and PNG are allowed.", 415)

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        return error_response("Unsupported content type. Only image/jpeg and image/png are allowed.", 415)

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return error_response("File exceeds 2 MB size limit.", 413)

    try:
        s3_service = get_s3_service()
        object_key = s3_service.upload_bytes(file_bytes, extension, content_type)
        settings = get_settings()
    except ValueError as exc:
        return error_response(str(exc), 500)
    except Exception:
        return error_response("S3 upload failed.", 500)

    response = {"url": f"https://{settings.s3_bucket_name}.s3.amazonaws.com/{object_key}"}
    if BACKEND_PORT:
        response["backend_port"] = BACKEND_PORT

    return response
