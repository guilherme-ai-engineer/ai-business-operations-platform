from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from dependencies import get_current_admin
from models import User
from rag_service import invalidate_knowledge_index


router = APIRouter(
    tags=["Knowledge Base"],
)


KNOWLEDGE_BASE_DIR = Path("knowledge_base")
KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)

MAX_DOCUMENT_SIZE = 10_000_000


@router.post(
    "/documents",
    summary="Upload a RAG document",
)
async def upload_document(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
):
    filename = Path(
        file.filename or ""
    ).name

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in {".txt", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only .txt and .pdf files "
                "are supported."
            ),
        )

    content = await file.read()

    if len(content) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File is too large.",
        )

    if extension == ".txt":
        try:
            content.decode("utf-8")

        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The text file must use "
                    "UTF-8 encoding."
                ),
            )

    file_path = (
        KNOWLEDGE_BASE_DIR / filename
    )

    file_path.write_bytes(content)

    invalidate_knowledge_index()

    return {
        "filename": filename,
        "status": "uploaded",
        "rag_index": (
            "will rebuild on next query"
        ),
    }