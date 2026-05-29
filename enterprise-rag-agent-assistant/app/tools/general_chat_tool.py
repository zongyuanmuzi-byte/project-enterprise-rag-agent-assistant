from app.services.llm_service import LLMClient
from app.tools.base import BaseTool


class GeneralChatTool(BaseTool):
    name = "general_chat_tool"
    description = "Handle general conversation when no specialized tool is needed."
    input_schema = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "User general chat message.",
            }
        },
        "required": ["question"],
    }

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, tool_input: dict) -> dict:
        question = tool_input.get("question", "").strip()

        if not question:
            return {
                "output": "",
                "sources": [],
                "error": "general_chat_tool input cannot be empty.",
            }

        prompt = f"""
你是一个友好、清晰、可靠的 AI 助手。

请回答用户的问题。

用户问题：
{question}
""".strip()

        try:
            answer = self.llm_client.generate_answer(prompt)

            return {
                "output": answer,
                "sources": [],
                "error": None,
            }

        except Exception as exc:
            return {
                "output": "",
                "sources": [],
                "error": f"general_chat_tool failed: {str(exc)}",
            }