import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["CHROMA_PATH"] = "data/test_chroma_db"

from fastapi.testclient import TestClient

from app.main import app


def test_document_upload_endpoint_accepts_markdown_file():
    client = TestClient(app)

    files = {
        "file": (
            "test_policy.md",
            b"# Test Policy\n\nRefund requests are reviewed before finance processing.",
            "text/markdown",
        )
    }

    response = client.post("/documents/upload", files=files)

    assert response.status_code == 200

    data = response.json()
    assert "document_id" in data
    assert data["filename"].endswith(".md")
    assert "chunks_count" in data
    assert "status" in data
