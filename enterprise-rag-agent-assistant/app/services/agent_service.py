import json
import time
import uuid
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agent.executor import ToolExecutor
from app.agent.router import AgentRouter
from app.database.models import ChatLog
from app.utils.logger import get_logger


logger = get_logger(__name__)


class AgentService:
    """
    Mainline Agent orchestration service.

    Flow:
        question -> AgentRouter -> ToolExecutor -> normalized result -> chat_logs
    """

    def __init__(self) -> None:
        self.router = AgentRouter()
        self.executor = ToolExecutor()

    def chat(
        self,
        question: str,
        db: Session,
        top_k: int | None = None,
    ) -> dict[str, Any]:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        cleaned_question = question.strip() if question else ""
        intent = "general_chat"
        tool_used = ""
        answer = ""
        sources: list[dict[str, Any]] = []
        error_message = None

        try:
            if not cleaned_question:
                raise ValueError("question cannot be empty.")

            route_result = self.router.route(cleaned_question)
            intent = route_result.get("intent", "general_chat")

            tool_result = self.executor.execute(
                intent=intent,
                question=cleaned_question,
                top_k=top_k,
                db=db,
            )

            tool_used = tool_result.get("tool_used", "")
            answer = tool_result.get("answer", "")
            sources = tool_result.get("sources", []) or []
            error_message = tool_result.get("error")

            latency_ms = int((time.time() - start_time) * 1000)

            self.save_chat_log_safely(
                db=db,
                request_id=request_id,
                question=cleaned_question,
                answer=answer,
                intent=intent,
                tool_used=tool_used,
                sources=sources,
                latency_ms=latency_ms,
                error_message=error_message,
            )

            logger.info(
                "Agent chat completed | request_id=%s | intent=%s | tool_used=%s | latency_ms=%s | error=%s",
                request_id,
                intent,
                tool_used,
                latency_ms,
                error_message,
            )

            return {
                "intent": intent,
                "tool_used": tool_used,
                "answer": answer,
                "sources": sources,
                "request_id": request_id,
                "latency_ms": latency_ms,
                "error": error_message,
            }

        except Exception as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            error_message = f"agent_chat failed: {str(exc)}"

            logger.exception(
                "Agent chat failed | request_id=%s | error_message=%s",
                request_id,
                error_message,
            )

            self.save_chat_log_safely(
                db=db,
                request_id=request_id,
                question=cleaned_question,
                answer="",
                intent=intent,
                tool_used=tool_used,
                sources=sources,
                latency_ms=latency_ms,
                error_message=error_message,
            )

            return {
                "intent": intent,
                "tool_used": tool_used,
                "answer": "",
                "sources": [],
                "request_id": request_id,
                "latency_ms": latency_ms,
                "error": error_message,
            }

    def save_chat_log_safely(
        self,
        db: Session,
        request_id: str,
        question: str,
        answer: str | None,
        intent: str | None,
        tool_used: str | None,
        sources: list,
        latency_ms: int,
        error_message: str | None,
    ) -> None:
        try:
            chat_log = ChatLog(
                request_id=request_id,
                question=question,
                answer=answer,
                intent=intent,
                tool_used=tool_used,
                retrieved_chunks=json.dumps(
                    sources,
                    ensure_ascii=False,
                ),
                latency_ms=latency_ms,
                error_message=error_message,
            )

            db.add(chat_log)
            db.commit()

        except SQLAlchemyError as exc:
            db.rollback()

            logger.exception(
                "Failed to save agent chat log | request_id=%s | error_message=%s",
                request_id,
                str(exc),
            )
