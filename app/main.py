"""FastAPI application entrypoint."""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Simple readiness endpoint."""
    return {"status": "ok"}


def error_response(message: str, status_code: int) -> JSONResponse:
    """Return a consistent error payload."""
    return JSONResponse(status_code=status_code, content={"error": message})


@app.post("/upload")
async def upload_file(file: UploadFile | None = File(default=None)) -> dict[str, str] | JSONResponse:
    """Upload endpoint skeleton with initial validation."""
    if file is None:
        return error_response("No file uploaded", 400)

    return {"filename": file.filename or "unknown"}
