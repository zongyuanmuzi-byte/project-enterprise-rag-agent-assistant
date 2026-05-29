from app.config import settings
from app.services.rag_service import NO_RELEVANT_CONTEXT_ANSWER, RAGService


class FakeEmbeddingClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVectorStore:
    def __init__(self, chunks: list[dict]):
        self.chunks = chunks

    def count(self) -> int:
        return len(self.chunks)

    def search_similar_chunks(self, query_embedding: list[float], top_k: int | None = None):
        return self.chunks[:top_k]


class FakeLLMClient:
    def generate_answer(self, prompt: str) -> str:
        return "Refunds are processed after review."


class FakeDB:
    def __init__(self):
        self.items = []

    def add(self, item):
        self.items.append(item)

    def commit(self):
        pass

    def rollback(self):
        pass


def build_rag_service(chunks: list[dict]) -> RAGService:
    service = RAGService.__new__(RAGService)
    service.embedding_client = FakeEmbeddingClient()
    service.vector_store = FakeVectorStore(chunks)
    service.llm_client = FakeLLMClient()
    return service


def test_document_outside_question_returns_no_answer(monkeypatch):
    monkeypatch.setattr(settings, "min_relevance_score", 0.8)

    service = build_rag_service(
        [
            {
                "content": "Refund policy content.",
                "filename": "policy.md",
                "chunk_index": 0,
                "document_id": 1,
                "distance": 10.0,
                "relevance_score": 0.09,
            }
        ]
    )

    result = service.chat(
        question="Where is the annual party?",
        top_k=1,
        db=FakeDB(),
    )

    assert result["answer"] == NO_RELEVANT_CONTEXT_ANSWER
    assert result["sources"] == []


def test_document_inside_question_keeps_sources(monkeypatch):
    monkeypatch.setattr(settings, "min_relevance_score", 0.8)

    service = build_rag_service(
        [
            {
                "content": "Refund requests are reviewed before finance processing.",
                "filename": "policy.md",
                "chunk_index": 0,
                "document_id": 1,
                "distance": 0.1,
                "relevance_score": 0.91,
            }
        ]
    )

    result = service.chat(
        question="What is the refund policy?",
        top_k=1,
        db=FakeDB(),
    )

    assert result["answer"] == "Refunds are processed after review."
    assert len(result["sources"]) == 1
    assert result["sources"][0]["relevance_score"] == 0.91
