"""FastAPI application entrypoint."""

from fastapi import FastAPI, File, UploadFile

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    """Simple readiness endpoint."""
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    """Upload endpoint skeleton; validation and S3 integration come next."""
    return {"filename": file.filename or "unknown"}
