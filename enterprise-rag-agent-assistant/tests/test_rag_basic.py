import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["CHROMA_PATH"] = "data/test_chroma_db"

from fastapi.testclient import TestClient

from app.main import app


def test_chat_response_shape():
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "question": "What is the refund policy?",
            "top_k": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "request_id" in data
    assert "latency_ms" in data
    assert isinstance(data["sources"], list)
