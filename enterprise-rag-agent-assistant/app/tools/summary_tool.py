from app.services.llm_service import LLMClient
from app.tools.base import BaseTool


class SummaryTool(BaseTool):
    name = "summary_tool"
    description = "Summarize user-provided text."
    input_schema = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "User text or instruction to summarize.",
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
                "error": "summary_tool input cannot be empty.",
            }

        if len(question) < 20:
            return {
                "output": "",
                "sources": [],
                "error": "summary_tool input is too short to summarize.",
            }

        prompt = f"""
你是一个企业 AI 助手，请帮用户总结下面内容。

要求：
1. 用中文回答。
2. 提炼核心观点。
3. 不要编造原文没有的信息。
4. 如果内容很短，请给出简洁总结。

用户内容：
{question}

请输出总结：
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
                "error": f"summary_tool failed: {str(exc)}",
            }