from app.services.llm_service import LLMClient
from app.tools.base import BaseTool


class WritingTool(BaseTool):
    name = "writing_tool"
    description = "Write or rewrite emails, copywriting, notices, and explanations."
    input_schema = {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "User writing instruction.",
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
                "error": "writing_tool instruction cannot be empty.",
            }

        prompt = f"""
你是一个专业的企业写作助手。

请根据用户要求完成写作任务。

要求：
1. 内容清晰、自然、礼貌。
2. 如果用户要求写邮件，请给出主题和正文。
3. 如果用户要求写说明或文案，请结构清楚。
4. 不要编造用户没有提供的具体事实。
5. 默认用中文输出，除非用户明确要求英文。

用户要求：
{question}

请输出结果：
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
                "error": f"writing_tool failed: {str(exc)}",
            }