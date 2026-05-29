from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import DocumentIndexRequest, DocumentIndexResponse
from app.services.document_service import (
    SUPPORTED_EXTENSIONS,
    index_document_for_rag,
    index_uploaded_document_for_rag,
)
from app.services.storage_service import get_storage_service
from app.utils.logger import get_logger


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

logger = get_logger(__name__)

@router.post("/index", response_model=DocumentIndexResponse, include_in_schema=False)
def index_document(
    request: DocumentIndexRequest,
    db: Session = Depends(get_db),
):
    """
    Development endpoint: index a local .txt, .md, or .pdf document path.

    The main user-facing ingestion endpoint is /documents/upload.
    """
    try:
        result = index_document_for_rag(
            file_path=request.file_path,
            db=db,
        )

        return DocumentIndexResponse(**result)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unknown server error when indexing document.",
        ) from exc


@router.post("/upload", response_model=DocumentIndexResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and index a .txt, .md, or text-based .pdf document.
    """
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="filename cannot be empty.",
        )

    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {file_extension}. "
                "Only .txt, .md, and .pdf files are supported."
            ),
        )

    try:
        storage_service = get_storage_service()
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file content is empty.",
            )

        storage_result = await storage_service.save_file(
            filename=original_filename,
            content=content,
            content_type=file.content_type,
        )

        result = index_uploaded_document_for_rag(
            filename=storage_result.filename,
            content=content,
            storage_path=storage_result.storage_path,
            db=db,
            content_type=file.content_type,
        )

        return DocumentIndexResponse(**result)

    except HTTPException:
        raise

    except ValueError as exc:
        logger.exception(
            "Validation error when uploading and indexing document | filename=%s",
            original_filename,
        )
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        logger.exception(
            "Runtime error when uploading and indexing document | filename=%s",
            original_filename,
        )
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unknown server error when uploading and indexing document | filename=%s",
            original_filename,
        )
        raise HTTPException(
            status_code=500,
            detail="Unknown server error when uploading and indexing document.",
        ) from exc
