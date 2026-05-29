from pathlib import Path
from io import BytesIO
import re
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app.config import settings
from app.database.models import Chunk, Document
from app.utils.logger import get_logger
from app.services.embedding_service import EmbeddingClient
from app.services.vector_store_service import VectorStoreService


logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def read_pdf_text_from_bytes(content: bytes, filename: str) -> str:
    """
    Extract text from a text-based PDF byte stream.
    """
    header = content[:5]

    if header != b"%PDF-":
        raise ValueError(
            f"Invalid PDF file: {filename}. "
            f"Expected file header to start with %PDF-, got {header!r}. "
            "Please make sure this is a real PDF file, not a renamed text file."
        )

    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        logger.exception("Failed to open PDF bytes | filename=%s", filename)
        raise RuntimeError(
            f"Failed to open PDF file: {filename}. Error: {str(exc)}"
        ) from exc

    if not reader.pages:
        raise ValueError(f"PDF has no pages: {filename}")

    page_texts: list[str] = []

    for page_index, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            logger.warning(
                "Failed to extract text from PDF page | filename=%s | page_index=%s | error=%s",
                filename,
                page_index,
                str(exc),
            )
            text = ""

        if text.strip():
            page_texts.append(text.strip())

    full_text = "\n\n".join(page_texts).strip()

    if not full_text:
        raise ValueError(
            f"No extractable text found in PDF: {filename}. "
            "This may be a scanned PDF and OCR is not supported at this stage."
        )

    logger.info(
        "PDF text extracted successfully | filename=%s | pages=%s | text_length=%s",
        filename,
        len(reader.pages),
        len(full_text),
    )

    return full_text


def read_file_content(
    filename: str,
    content: bytes,
    content_type: str | None = None,
) -> tuple[str, str]:
    """
    Read uploaded .txt, .md, or text-based .pdf content from bytes.
    """
    safe_filename = Path(filename).name

    if not safe_filename:
        raise ValueError("filename cannot be empty.")

    if not content:
        raise ValueError(f"File content is empty: {safe_filename}")

    file_extension = Path(safe_filename).suffix.lower()

    if file_extension not in SUPPORTED_EXTENSIONS:
        logger.error("Unsupported file type: %s", file_extension)
        raise ValueError(
            f"Unsupported file type: {file_extension}. "
            "Only .txt, .md, and text-based .pdf files are supported at this stage."
        )

    try:
        if file_extension == ".pdf":
            raw_text = read_pdf_text_from_bytes(content, safe_filename)
        else:
            raw_text = content.decode("utf-8")

    except UnicodeDecodeError as exc:
        logger.exception("Failed to decode uploaded file as UTF-8 | filename=%s", safe_filename)
        raise RuntimeError(
            f"Failed to read file as UTF-8. Please check file encoding: {safe_filename}"
        ) from exc

    except ValueError:
        raise

    except Exception as exc:
        logger.exception("Failed to read uploaded file bytes | filename=%s", safe_filename)
        raise RuntimeError(
            f"Failed to read uploaded file: {safe_filename}. Error: {str(exc)}"
        ) from exc

    if not raw_text.strip():
        logger.error("File content is empty after parsing | filename=%s", safe_filename)
        raise ValueError(f"File content is empty: {safe_filename}")

    logger.info(
        "Uploaded file bytes read successfully | filename=%s | file_type=%s | text_length=%s | content_type=%s",
        safe_filename,
        file_extension,
        len(raw_text),
        content_type,
    )

    return safe_filename, raw_text

def read_pdf_text(file_path: str) -> str:
    """
    Extract text from a text-based PDF file.

    This function does not support OCR.
    It only works when the PDF contains selectable text.
    """
    with open(file_path, "rb") as file:
        header = file.read(5)

    if header != b"%PDF-":
        raise ValueError(
            f"Invalid PDF file: {file_path}. "
            f"Expected file header to start with %PDF-, got {header!r}. "
            "Please make sure this is a real PDF file, not a renamed text file."
        )

    try:
        reader = PdfReader(file_path)
    except Exception as exc:
        logger.exception("Failed to open PDF file: %s", file_path)
        raise RuntimeError(
            f"Failed to open PDF file: {file_path}. Error: {str(exc)}"
        ) from exc

    if not reader.pages:
        raise ValueError(f"PDF has no pages: {file_path}")

    page_texts: list[str] = []

    for page_index, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            logger.warning(
                "Failed to extract text from PDF page | file_path=%s | page_index=%s | error=%s",
                file_path,
                page_index,
                str(exc),
            )
            text = ""

        if text.strip():
            page_texts.append(text.strip())

    full_text = "\n\n".join(page_texts).strip()

    if not full_text:
        raise ValueError(
            f"No extractable text found in PDF: {file_path}. "
            "This may be a scanned PDF and OCR is not supported at this stage."
        )

    logger.info(
        "PDF text extracted successfully | file_path=%s | pages=%s | text_length=%s",
        file_path,
        len(reader.pages),
        len(full_text),
    )

    return full_text


def read_file(file_path: str) -> tuple[str, str]:
    """
    Read a .txt, .md, or text-based .pdf file from the local file system.

    Args:
        file_path: Example:
            data/sample_docs/company_policy.md
            data/sample_docs/company_policy.pdf

    Returns:
        tuple:
            filename: The file name
            raw_text: The extracted text content
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise ValueError(f"Path is not a file: {file_path}")

    file_extension = path.suffix.lower()

    if file_extension not in SUPPORTED_EXTENSIONS:
        logger.error("Unsupported file type: %s", file_extension)
        raise ValueError(
            f"Unsupported file type: {file_extension}. "
            "Only .txt, .md, and text-based .pdf files are supported at this stage."
        )

    try:
        if file_extension == ".pdf":
            raw_text = read_pdf_text(str(path))
        else:
            raw_text = path.read_text(encoding="utf-8")

    except UnicodeDecodeError as exc:
        logger.exception("Failed to decode file as UTF-8: %s", file_path)
        raise RuntimeError(
            f"Failed to read file as UTF-8. Please check file encoding: {file_path}"
        ) from exc

    except ValueError:
        # Keep clear PDF extraction errors, such as:
        # scanned PDF / no extractable text / empty PDF.
        raise

    except Exception as exc:
        logger.exception("Failed to read file: %s", file_path)
        raise RuntimeError(
            f"Failed to read file: {file_path}. Error: {str(exc)}"
        ) from exc

    if not raw_text.strip():
        logger.error("File content is empty: %s", file_path)
        raise ValueError(f"File content is empty: {file_path}")

    logger.info(
        "File read successfully | file_path=%s | file_type=%s | text_length=%s",
        file_path,
        file_extension,
        len(raw_text),
    )

    return path.name, raw_text

def clean_text(text: str) -> str:
    """
    Clean raw text for RAG indexing.

    Current cleaning strategy:
    1. Normalize line breaks.
    2. Strip leading and trailing spaces from each line.
    3. Compress too many blank lines.
    4. Keep paragraph structure.

    Important:
    Do not clean too aggressively, otherwise useful semantic structure may be lost.
    """
    if not text or not text.strip():
        return ""

    # Normalize line breaks from Windows/Mac/Linux formats.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove leading and trailing spaces for each line.
    lines = [line.strip() for line in text.split("\n")]

    # Join lines back.
    text = "\n".join(lines)

    # Compress 3 or more consecutive newlines into 2 newlines.
    # This keeps paragraph separation while removing excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_text(
    text: str,
    document_id: int,
    filename: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict[str, Any]]:
    """
    Split cleaned text into chunks.

    Args:
        text: Cleaned text.
        document_id: The related document ID. At this step, we can temporarily use 0.
        filename: Source filename.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlapping characters between neighboring chunks.

    Returns:
        A list of chunk dictionaries:
        [
            {
                "content": "...",
                "chunk_index": 0,
                "metadata": {
                    "document_id": 1,
                    "filename": "company_policy.md",
                    "chunk_index": 0
                }
            }
        ]
    """
    if chunk_size is None:
        chunk_size = settings.chunk_size

    if chunk_overlap is None:
        chunk_overlap = settings.chunk_overlap

    if not text or not text.strip():
        raise ValueError("Text cannot be empty when splitting into chunks.")

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    chunks: list[dict[str, Any]] = []

    start = 0
    chunk_index = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk_content = text[start:end].strip()

        if chunk_content:
            chunks.append(
                {
                    "content": chunk_content,
                    "chunk_index": chunk_index,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": chunk_index,
                    },
                }
            )

            chunk_index += 1

        start += chunk_size - chunk_overlap

    logger.info(
        "Text split completed | filename=%s | document_id=%s | chunks_count=%s",
        filename,
        document_id,
        len(chunks),
    )

    return chunks


def preview_document_chunks(file_path: str) -> dict[str, Any]:
    """
    Preview the document reading, cleaning, and chunking result.

    This is a temporary helper function for Stage 2 Step 4.
    Later, /documents/index will use similar logic and then save data into:
    1. SQLite documents table
    2. SQLite chunks table
    3. Chroma vector store
    """
    filename, raw_text = read_file(file_path)
    cleaned_text = clean_text(raw_text)

    chunks = split_text(
        text=cleaned_text,
        document_id=0,
        filename=filename,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    return {
        "filename": filename,
        "raw_text_length": len(raw_text),
        "cleaned_text_length": len(cleaned_text),
        "chunks_count": len(chunks),
        "chunks": chunks,
    }
def index_document_to_sql(file_path: str, db: Session) -> dict[str, Any]:
    """
    Index a document into SQLite.

    This function only saves data into:
    1. documents table
    2. chunks table

    It does not create embeddings or write to Chroma yet.
    Chroma indexing will be added in the next steps.

    Args:
        file_path: Example: data/sample_docs/company_policy.md
        db: SQLAlchemy database session

    Returns:
        {
            "document_id": 1,
            "filename": "company_policy.md",
            "chunks_count": 3,
            "status": "indexed_to_sql"
        }
    """
    try:
        filename, raw_text = read_file(file_path)
        cleaned_text = clean_text(raw_text)

        path = Path(file_path)

        document = Document(
            filename=filename,
            file_path=str(path),
            file_type=path.suffix.lower().replace(".", ""),
        )

        db.add(document)

        # flush 会把 document 插入数据库，但还不会最终 commit。
        # 这样我们可以先拿到 document.id，用来关联 chunks。
        db.flush()

        chunks = split_text(
            text=cleaned_text,
            document_id=document.id,
            filename=filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        chunk_models = []

        for chunk in chunks:
            chunk_model = Chunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
            )
            chunk_models.append(chunk_model)

        db.add_all(chunk_models)
        db.commit()
        db.refresh(document)

        logger.info(
            "Document indexed to SQL successfully | document_id=%s | filename=%s | chunks_count=%s",
            document.id,
            filename,
            len(chunks),
        )

        return {
            "document_id": document.id,
            "filename": filename,
            "chunks_count": len(chunks),
            "status": "indexed_to_sql",
        }

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error when indexing document | file_path=%s",
            file_path,
        )

        raise RuntimeError(
            f"Database error when indexing document: {str(exc)}"
        ) from exc

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to index document to SQL | file_path=%s",
            file_path,
        )

        raise
    
    
def index_document_for_rag(file_path: str, db: Session) -> dict[str, Any]:
    """
    Index a document into both SQLite and Chroma.

    Full Stage 2 indexing flow:
    1. Read local .txt / .md file
    2. Clean text
    3. Create document record in SQLite
    4. Split text into chunks
    5. Save chunks into SQLite
    6. Generate embeddings for chunks
    7. Save chunks + embeddings + metadata into Chroma
    8. Commit SQL transaction

    Args:
        file_path: Example: data/sample_docs/company_policy.md
        db: SQLAlchemy database session

    Returns:
        {
            "document_id": 1,
            "filename": "company_policy.md",
            "chunks_count": 3,
            "status": "indexed"
        }
    """
    try:
        filename, raw_text = read_file(file_path)
        cleaned_text = clean_text(raw_text)

        path = Path(file_path)

        document = Document(
            filename=filename,
            file_path=str(path),
            file_type=path.suffix.lower().replace(".", ""),
        )

        db.add(document)

        # We need document.id before creating chunks and Chroma IDs.
        db.flush()

        chunks = split_text(
            text=cleaned_text,
            document_id=document.id,
            filename=filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        chunk_models = []

        for chunk in chunks:
            chunk_model = Chunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
            )
            chunk_models.append(chunk_model)

        db.add_all(chunk_models)

        # Generate embeddings for all chunk contents.
        embedding_client = EmbeddingClient()
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_client.embed_texts(chunk_texts)

        # Save chunks and embeddings into Chroma.
        vector_store = VectorStoreService()
        vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        db.commit()
        db.refresh(document)

        logger.info(
            "Document indexed for RAG successfully | document_id=%s | filename=%s | chunks_count=%s",
            document.id,
            filename,
            len(chunks),
        )

        return {
            "document_id": document.id,
            "filename": filename,
            "chunks_count": len(chunks),
            "status": "indexed",
        }

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error when indexing document for RAG | file_path=%s",
            file_path,
        )

        raise RuntimeError(
            f"Database error when indexing document for RAG: {str(exc)}"
        ) from exc

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to index document for RAG | file_path=%s",
            file_path,
        )

        raise   


def index_uploaded_document_for_rag(
    filename: str,
    content: bytes,
    storage_path: str,
    db: Session,
    content_type: str | None = None,
) -> dict[str, Any]:
    """
    Index an uploaded document from bytes into both SQLite and Chroma.

    This path is used by /documents/upload so cloud storage providers such as
    COS do not need to provide a local readable file path.
    """
    try:
        filename, raw_text = read_file_content(
            filename=filename,
            content=content,
            content_type=content_type,
        )
        cleaned_text = clean_text(raw_text)

        file_extension = Path(filename).suffix.lower()

        document = Document(
            filename=filename,
            file_path=storage_path,
            file_type=file_extension.replace(".", ""),
        )

        db.add(document)
        db.flush()

        chunks = split_text(
            text=cleaned_text,
            document_id=document.id,
            filename=filename,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        chunk_models = []

        for chunk in chunks:
            chunk_model = Chunk(
                document_id=document.id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
            )
            chunk_models.append(chunk_model)

        db.add_all(chunk_models)

        embedding_client = EmbeddingClient()
        chunk_texts = [chunk["content"] for chunk in chunks]
        embeddings = embedding_client.embed_texts(chunk_texts)

        vector_store = VectorStoreService()
        vector_store.add_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        db.commit()
        db.refresh(document)

        logger.info(
            "Uploaded document indexed for RAG successfully | document_id=%s | filename=%s | storage_path=%s | chunks_count=%s",
            document.id,
            filename,
            storage_path,
            len(chunks),
        )

        return {
            "document_id": document.id,
            "filename": filename,
            "chunks_count": len(chunks),
            "status": "indexed",
        }

    except SQLAlchemyError as exc:
        db.rollback()

        logger.exception(
            "Database error when indexing uploaded document for RAG | filename=%s | storage_path=%s",
            filename,
            storage_path,
        )

        raise RuntimeError(
            f"Database error when indexing uploaded document for RAG: {str(exc)}"
        ) from exc

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to index uploaded document for RAG | filename=%s | storage_path=%s",
            filename,
            storage_path,
        )

        raise
