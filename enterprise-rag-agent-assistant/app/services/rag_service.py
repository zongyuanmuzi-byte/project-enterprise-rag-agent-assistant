import json
import time
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import ChatLog
from app.prompts.rag_prompt import build_context_from_chunks, build_rag_prompt
from app.services.embedding_service import EmbeddingClient
from app.services.llm_service import LLMClient
from app.services.vector_store_service import VectorStoreService
from app.utils.logger import get_logger


logger = get_logger(__name__)

EMPTY_VECTOR_STORE_ERROR_CODE = "EMPTY_VECTOR_STORE"
NO_RELEVANT_CONTEXT_ERROR_CODE = "NO_RELEVANT_CONTEXT"

EMPTY_VECTOR_STORE_ANSWER = (
    "\u5f53\u524d\u77e5\u8bc6\u5e93\u8fd8\u6ca1\u6709\u53ef\u68c0\u7d22\u5185\u5bb9"
    "\uff0c\u8bf7\u5148\u4e0a\u4f20\u6587\u6863\u540e\u518d\u63d0\u95ee\u3002"
)
NO_RELEVANT_CONTEXT_ANSWER = (
    "\u6839\u636e\u5f53\u524d\u77e5\u8bc6\u5e93\u8d44\u6599\uff0c"
    "\u65e0\u6cd5\u56de\u7b54\u8be5\u95ee\u9898\u3002"
)


class RAGService:
    """
    RAG question-answering service.

    Full flow:
    1. Validate question
    2. Embed question
    3. Retrieve top-k chunks from Chroma
    4. Build context
    5. Build RAG prompt
    6. Generate answer with LLM
    7. Save chat log
    8. Return answer + sources
    """

    def __init__(self) -> None:
        self.embedding_client = EmbeddingClient()
        self.vector_store = VectorStoreService()
        self.llm_client = LLMClient()

    def chat(
        self,
        question: str,
        db: Session,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        cleaned_question = question.strip() if question else ""

        if not cleaned_question:
            raise ValueError("question cannot be empty.")

        if top_k is None:
            top_k = settings.default_top_k

        try:
            if self.vector_store.count() == 0:
                latency_ms = int((time.time() - start_time) * 1000)

                self._save_chat_log_safely(
                    db=db,
                    request_id=request_id,
                    question=cleaned_question,
                    answer=EMPTY_VECTOR_STORE_ANSWER,
                    retrieved_chunks=[],
                    latency_ms=latency_ms,
                    error_message=EMPTY_VECTOR_STORE_ERROR_CODE,
                )

                logger.warning(
                    "RAG chat warning | request_id=%s | question=%s | error_code=%s",
                    request_id,
                    cleaned_question,
                    EMPTY_VECTOR_STORE_ERROR_CODE,
                )

                return {
                    "answer": EMPTY_VECTOR_STORE_ANSWER,
                    "sources": [],
                    "request_id": request_id,
                    "latency_ms": latency_ms,
                }

            query_embedding = self.embedding_client.embed_texts([cleaned_question])[0]

            retrieved_chunks = self.vector_store.search_similar_chunks(
                query_embedding=query_embedding,
                top_k=top_k,
            )

            relevant_chunks = self._filter_relevant_chunks(retrieved_chunks)

            if not relevant_chunks:
                answer = NO_RELEVANT_CONTEXT_ANSWER
                sources = []
                error_code = NO_RELEVANT_CONTEXT_ERROR_CODE
            else:
                context = build_context_from_chunks(relevant_chunks)
                prompt = build_rag_prompt(
                    context=context,
                    question=cleaned_question,
                )

                answer = self.llm_client.generate_answer(prompt)
                sources = self._build_sources(relevant_chunks)
                error_code = None

            latency_ms = int((time.time() - start_time) * 1000)

            if error_code is None:
                self._save_chat_log(
                    db=db,
                    request_id=request_id,
                    question=cleaned_question,
                    answer=answer,
                    retrieved_chunks=sources,
                    latency_ms=latency_ms,
                    error_message=error_code,
                )
            else:
                self._save_chat_log_safely(
                    db=db,
                    request_id=request_id,
                    question=cleaned_question,
                    answer=answer,
                    retrieved_chunks=sources,
                    latency_ms=latency_ms,
                    error_message=error_code,
                )

            if error_code == NO_RELEVANT_CONTEXT_ERROR_CODE:
                logger.warning(
                    "RAG chat warning | request_id=%s | question=%s | error_code=%s | min_relevance_score=%s | raw_chunks=%s",
                    request_id,
                    cleaned_question,
                    NO_RELEVANT_CONTEXT_ERROR_CODE,
                    settings.min_relevance_score,
                    len(retrieved_chunks),
                )

            logger.info(
                "RAG chat completed | request_id=%s | top_k=%s | retrieved_chunks=%s | latency_ms=%s",
                request_id,
                top_k,
                len(sources),
                latency_ms,
            )

            return {
                "answer": answer,
                "sources": sources,
                "request_id": request_id,
                "latency_ms": latency_ms,
            }

        except ValueError as exc:
            latency_ms = int((time.time() - start_time) * 1000)

            self._save_chat_log_safely(
                db=db,
                request_id=request_id,
                question=cleaned_question,
                answer=None,
                retrieved_chunks=[],
                latency_ms=latency_ms,
                error_message=str(exc),
            )

            logger.warning(
                "RAG chat value error | request_id=%s | error_message=%s",
                request_id,
                str(exc),
            )

            raise

        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)

            self._save_chat_log_safely(
                db=db,
                request_id=request_id,
                question=cleaned_question,
                answer=None,
                retrieved_chunks=[],
                latency_ms=latency_ms,
                error_message=str(exc),
            )

            logger.exception(
                "RAG chat failed | request_id=%s | error_message=%s",
                request_id,
                str(exc),
            )

            raise RuntimeError(f"RAG chat failed: {str(exc)}") from exc

    def _build_sources(self, retrieved_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Convert retrieved chunks into API sources.
        """
        sources = []

        for chunk in retrieved_chunks:
            sources.append(
                {
                    "filename": chunk.get("filename"),
                    "chunk_index": chunk.get("chunk_index"),
                    "document_id": chunk.get("document_id"),
                    "content": chunk.get("content", ""),
                    "distance": chunk.get("distance"),
                    "relevance_score": chunk.get("relevance_score"),
                }
            )

        return sources

    def _filter_relevant_chunks(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Keep only chunks whose relevance_score passes MIN_RELEVANCE_SCORE.
        """
        if not chunks:
            return []

        filtered_chunks = []

        for chunk in chunks:
            relevance_score = chunk.get("relevance_score")

            if relevance_score is None:
                relevance_score = self._distance_to_relevance_score(chunk.get("distance"))
                chunk["relevance_score"] = relevance_score

            if float(relevance_score) >= settings.min_relevance_score:
                filtered_chunks.append(chunk)

        logger.info(
            "RAG relevance filtering completed | raw_chunks=%s | filtered_chunks=%s | min_relevance_score=%s",
            len(chunks),
            len(filtered_chunks),
            settings.min_relevance_score,
        )

        return filtered_chunks

    @staticmethod
    def _distance_to_relevance_score(distance: float | int | None) -> float:
        """
        Convert Chroma distance to relevance score.

        Chroma distance is smaller-is-better. relevance_score is larger-is-better.
        """
        if distance is None:
            return 0.0

        distance_value = float(distance)

        if distance_value < 0:
            distance_value = 0.0

        return 1.0 / (1.0 + distance_value)

    def _save_chat_log(
        self,
        db: Session,
        request_id: str,
        question: str,
        answer: str | None,
        retrieved_chunks: list[dict[str, Any]],
        latency_ms: int,
        error_message: str | None,
    ) -> None:
        """
        Save chat log into SQLite.
        """
        chat_log = ChatLog(
            request_id=request_id,
            question=question,
            answer=answer,
            intent="rag_chat",
            tool_used="vector_search",
            retrieved_chunks=json.dumps(
                retrieved_chunks,
                ensure_ascii=False,
            ),
            latency_ms=latency_ms,
            error_message=error_message,
        )

        db.add(chat_log)
        db.commit()

    def _save_chat_log_safely(
        self,
        db: Session,
        request_id: str,
        question: str,
        answer: str | None,
        retrieved_chunks: list[dict[str, Any]],
        latency_ms: int,
        error_message: str | None,
    ) -> None:
        """
        Save chat log safely even when main RAG flow fails.
        """
        try:
            self._save_chat_log(
                db=db,
                request_id=request_id,
                question=question,
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                latency_ms=latency_ms,
                error_message=error_message,
            )
        except SQLAlchemyError:
            db.rollback()
            logger.exception(
                "Failed to save error chat log | request_id=%s",
                request_id,
            )
