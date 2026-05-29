from sqlalchemy.orm import Session

from app.tools.general_chat_tool import GeneralChatTool
from app.tools.rag_tool import RAGTool
from app.tools.summary_tool import SummaryTool
from app.tools.writing_tool import WritingTool
from app.utils.logger import get_logger


logger = get_logger(__name__)


class ToolExecutor:
    """
    Mainline Agent tool executor.

    Execute tools according to intent and normalize tool results.
    """

    def __init__(self) -> None:
        self.intent_to_tool = {
            "document_qa": RAGTool(),
            "summary": SummaryTool(),
            "writing": WritingTool(),
            "general_chat": GeneralChatTool(),
        }

    def execute(
        self,
        intent: str,
        question: str,
        db: Session,
        top_k: int | None = None,
    ) -> dict:
        if not intent:
            return self._build_error_result(
                error="intent cannot be empty.",
                tool_used="",
            )

        tool = self.intent_to_tool.get(intent)

        if tool is None:
            logger.error("Tool not found for intent | intent=%s", intent)

            return self._build_error_result(
                error=f"tool not found for intent: {intent}",
                tool_used="",
            )

        tool_input = {
            "question": question,
            "top_k": top_k,
            "db": db,
        }

        try:
            result = tool.run(tool_input)

            if not isinstance(result, dict):
                return self._build_error_result(
                    error=f"{tool.name} returned invalid result type.",
                    tool_used=tool.name,
                )

            return {
                "tool_used": tool.name,
                "answer": result.get("output", "") or "",
                "sources": result.get("sources", []) or [],
                "error": result.get("error"),
            }

        except Exception as exc:
            logger.exception(
                "Tool execution failed | intent=%s | tool=%s | error=%s",
                intent,
                tool.name,
                str(exc),
            )

            return self._build_error_result(
                error=f"{tool.name} execution failed: {str(exc)}",
                tool_used=tool.name,
            )

    def _build_error_result(self, error: str, tool_used: str) -> dict:
        return {
            "tool_used": tool_used,
            "answer": "",
            "sources": [],
            "error": error,
        }
