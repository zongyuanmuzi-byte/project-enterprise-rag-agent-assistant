import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["CHROMA_PATH"] = "data/test_chroma_db"

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data or "message" in data
