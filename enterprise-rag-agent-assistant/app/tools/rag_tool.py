from sqlalchemy.orm import Session

from app.services.rag_service import RAGService
from app.tools.base import BaseTool


class RAGTool(BaseTool):
    name = "rag_tool"
    description = "Answer questions based on the enterprise knowledge base."
    input_schema = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "User question for the knowledge base.",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of chunks to retrieve.",
            },
            "db": {
                "type": "object",
                "description": "Database session.",
            },
        },
        "required": ["question", "db"],
    }

    def __init__(self) -> None:
        self.rag_service = RAGService()

    def run(self, tool_input: dict) -> dict:
        question = tool_input.get("question")
        top_k = tool_input.get("top_k")
        db: Session | None = tool_input.get("db")

        if not question or not question.strip():
            return {
                "output": "",
                "sources": [],
                "error": "question cannot be empty for rag_tool.",
            }

        if db is None:
            return {
                "output": "",
                "sources": [],
                "error": "db session is required for rag_tool.",
            }

        try:
            result = self.rag_service.chat(
                question=question,
                top_k=top_k,
                db=db,
            )

            sources = result.get("sources", [])

            if not sources:
                return {
                    "output": result.get("answer", "知识库中没有找到明确答案。"),
                    "sources": [],
                    "error": None,
                }

            return {
                "output": result.get("answer", ""),
                "sources": sources,
                "error": None,
            }

        except Exception as exc:
            return {
                "output": "",
                "sources": [],
                "error": f"rag_tool failed: {str(exc)}",
            }