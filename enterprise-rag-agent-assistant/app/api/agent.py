import time
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas import AgentChatRequest, AgentChatResponse
from app.services.agent_service import AgentService
from app.utils.logger import get_logger

router = APIRouter(tags=["Agent"])

logger = get_logger(__name__)

agent_service = AgentService()

@router.post("/agent/chat", response_model=AgentChatResponse)
def agent_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    result = agent_service.chat(
        question=request.question,
        top_k=request.top_k,
        db=db,
    )

    return AgentChatResponse(**result)

@router.post("/agent/graph-chat", response_model=AgentChatResponse, include_in_schema=False)
def agent_graph_chat(
    request: AgentChatRequest,
    db: Session = Depends(get_db),
):
    """
    Experimental LangGraph endpoint.

    The mainline Agent API is POST /agent/chat via AgentService.
    Keep this endpoint only for local experiments.
    """
    from app.services.langgraph_agent import LangGraphAgent

    langgraph_agent = LangGraphAgent()
    request_id = str(uuid.uuid4())
    start_time = time.time()

    question = request.question.strip()
    intent = "general_chat"
    tool_used = ""
    answer = ""
    sources = []
    error_message = None

    try:
        state = langgraph_agent.run(
            question=question,
            db=db,
            top_k=request.top_k,
        )

        intent = state.get("intent") or "general_chat"
        tool_used = state.get("tool_used") or ""
        answer = state.get("answer") or ""
        sources = state.get("sources") or []
        error_message = state.get("error")

        latency_ms = int((time.time() - start_time) * 1000)

        agent_service.save_chat_log_safely(
            db=db,
            request_id=request_id,
            question=question,
            answer=answer,
            intent=intent,
            tool_used=tool_used,
            sources=sources,
            latency_ms=latency_ms,
            error_message=error_message,
        )

        logger.info(
            "LangGraph agent chat completed | request_id=%s | intent=%s | tool_used=%s | latency_ms=%s | error=%s",
            request_id,
            intent,
            tool_used,
            latency_ms,
            error_message,
        )

        return AgentChatResponse(
            intent=intent,
            tool_used=tool_used,
            answer=answer,
            sources=sources,
            request_id=request_id,
            latency_ms=latency_ms,
            error=error_message,
        )

    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        error_message = f"langgraph agent chat failed: {str(exc)}"

        logger.exception(
            "LangGraph agent chat failed | request_id=%s | error_message=%s",
            request_id,
            error_message,
        )

        agent_service.save_chat_log_safely(
            db=db,
            request_id=request_id,
            question=question,
            answer="",
            intent=intent,
            tool_used=tool_used,
            sources=sources,
            latency_ms=latency_ms,
            error_message=error_message,
        )

        return AgentChatResponse(
            intent=intent,
            tool_used=tool_used,
            answer="",
            sources=[],
            request_id=request_id,
            latency_ms=latency_ms,
            error=error_message,
        )
