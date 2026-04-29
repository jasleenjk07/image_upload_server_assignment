"""FastAPI application entrypoint."""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024


@app.get("/health")
def health() -> dict[str, str]:
    """Simple readiness endpoint."""
    return {"status": "ok"}


def error_response(message: str, status_code: int) -> JSONResponse:
    """Return a consistent error payload."""
    return JSONResponse(status_code=status_code, content={"error": message})


@app.post("/upload")
async def upload_file(file: UploadFile | None = File(default=None)) -> dict[str, str]:
    """Upload endpoint skeleton with initial validation."""
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

    await file.seek(0)
    return {"filename": file.filename or "unknown"}
