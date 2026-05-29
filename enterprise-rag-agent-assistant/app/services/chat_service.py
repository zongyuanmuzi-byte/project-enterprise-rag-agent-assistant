import time
import uuid

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import ChatLog
from app.utils.logger import app_logger


class ChatService:
    def generate_placeholder_answer(self, question: str) -> str:
        """
        Generate a placeholder answer.

        In later stages, this method will be replaced by:
        1. RAG retrieval
        2. Prompt construction
        3. LLM generation
        4. Agent tool calling
        """
        return (
            "This is a placeholder answer. "
            "In the next stage, this endpoint will connect to the RAG pipeline."
        )

    def chat(self, question: str, db: Session) -> dict:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            if not question or not question.strip():
                raise ValueError("question cannot be empty.")

            cleaned_question = question.strip()
            answer = self.generate_placeholder_answer(cleaned_question)

            latency_ms = int((time.time() - start_time) * 1000)

            chat_log = ChatLog(
                request_id=request_id,
                question=cleaned_question,
                answer=answer,
                intent="basic_chat",
                tool_used="placeholder",
                latency_ms=latency_ms,
                error_message=None,
            )

            db.add(chat_log)
            db.commit()

            app_logger.info(
                "request_id=%s | question=%s | latency_ms=%s | error_message=%s",
                request_id,
                cleaned_question,
                latency_ms,
                None,
            )

            return {
                "answer": answer,
                "request_id": request_id,
                "latency_ms": latency_ms,
            }

        except SQLAlchemyError as exc:
            db.rollback()

            latency_ms = int((time.time() - start_time) * 1000)
            error_message = f"Database write failed: {str(exc)}"

            app_logger.error(
                "request_id=%s | question=%s | latency_ms=%s | error_message=%s",
                request_id,
                question,
                latency_ms,
                error_message,
            )

            raise RuntimeError(error_message) from exc

        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            error_message = str(exc)

            app_logger.error(
                "request_id=%s | question=%s | latency_ms=%s | error_message=%s",
                request_id,
                question,
                latency_ms,
                error_message,
            )

            raise
