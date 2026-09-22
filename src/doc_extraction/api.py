"""FastAPI service exposing POST /extract for structured document extraction."""

import tempfile
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

load_dotenv()

from doc_extraction.extraction import extract_document  # noqa: E402
from doc_extraction.schemas import DocumentType  # noqa: E402

app = FastAPI(title="Document Extraction Pipeline")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract")
async def extract(
    document_type: DocumentType,
    file: UploadFile = File(...),  # noqa: B008 -- FastAPI's documented pattern
) -> JSONResponse:
    if file.content_type not in ("image/png", "image/jpeg"):
        raise HTTPException(400, f"Unsupported content type: {file.content_type}")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        result = extract_document(tmp_path, document_type)
    finally:
        tmp_path.unlink(missing_ok=True)

    if result.validated is None:
        raise HTTPException(
            422,
            detail={
                "message": "Extraction did not pass validation",
                "error": result.error,
                "raw_output": result.raw_output,
            },
        )

    return JSONResponse(
        {
            "document_type": document_type.value,
            "data": result.validated.model_dump(),
            "valid_on_first_try": result.valid_on_first_try,
            "attempts": result.attempts,
            "latency_seconds": result.latency_seconds,
        }
    )
