from typing import Literal

from app.config import settings
from app.prompts.rag_prompt import NO_ANSWER_TEXT
from app.utils.logger import get_logger


logger = get_logger(__name__)


LLMProvider = Literal["mock", "openai_compatible"]


class LLMClient:
    """
    Unified LLM client.

    Supported providers:
    1. mock: local deterministic-ish responses for pipeline testing.
    2. openai_compatible: OpenAI-compatible chat completions API.
    """

    def __init__(self) -> None:
        self.provider: LLMProvider = settings.llm_provider  # type: ignore
        self.model = settings.llm_model
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.timeout_seconds = settings.llm_timeout_seconds

        if self.provider == "openai_compatible":
            if not self.api_key:
                raise ValueError(
                    "LLM_API_KEY is required when LLM_PROVIDER=openai_compatible."
                )

            from openai import OpenAI

            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout_seconds,
            }

            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self.client = OpenAI(**client_kwargs)
        else:
            self.client = None

    def generate_answer(self, prompt: str) -> str:
        """
        Generate plain text from a prompt.
        """
        if not prompt or not prompt.strip():
            raise ValueError("prompt cannot be empty.")

        try:
            if self.provider == "mock":
                return self._generate_answer_mock(prompt)

            if self.provider == "openai_compatible":
                return self._generate_answer_openai_compatible(prompt)

            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        except Exception as exc:
            logger.exception(
                "LLM generation failed | provider=%s | model=%s | error_type=%s",
                self.provider,
                self.model,
                type(exc).__name__,
            )
            raise RuntimeError("LLM generation failed.") from exc

    def _generate_answer_mock(self, prompt: str) -> str:
        """
        Mock LLM answer.

        This mode is for local engineering pipeline tests only. It does not call
        external APIs and does not represent real model quality.
        """
        logger.info("Mock LLM generated answer.")

        question = self._extract_question_from_prompt(prompt)

        if self._looks_like_router_prompt(prompt):
            return self._generate_router_json_mock(question or prompt)

        if self._contains_any(question, ["refund", "\u9000\u6b3e"]) or self._contains_any(prompt, ["7 "]):
            if "7" in prompt:
                return (
                    "\u6839\u636e\u77e5\u8bc6\u5e93\u8d44\u6599\uff0c"
                    "\u9000\u6b3e\u901a\u5e38\u4f1a\u5728\u5ba1\u6838\u901a\u8fc7\u540e"
                    "\u7531\u8d22\u52a1\u90e8\u95e8\u5904\u7406\uff0c\u5177\u4f53\u65f6\u95f4\u8bf7\u4ee5\u6587\u6863\u6761\u6b3e\u4e3a\u51c6\u3002"
                )

        if self._contains_any(prompt, ["summary", "\u603b\u7ed3", "\u6982\u62ec"]):
            return "\u8fd9\u662f mock \u6a21\u5f0f\u751f\u6210\u7684\u7b80\u8981\u603b\u7ed3\u3002"

        if self._contains_any(prompt, ["write", "email", "\u90ae\u4ef6", "\u5199"]):
            return "This is a mock draft generated for local testing."

        return NO_ANSWER_TEXT

    def _generate_answer_openai_compatible(self, prompt: str) -> str:
        """
        Call an OpenAI-compatible chat completions API.
        """
        if self.client is None:
            raise RuntimeError("OpenAI-compatible LLM client is not initialized.")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.2,
            )
        except Exception as exc:
            logger.exception(
                "OpenAI-compatible LLM request failed | provider=%s | model=%s | error_type=%s",
                self.provider,
                self.model,
                type(exc).__name__,
            )
            raise RuntimeError("OpenAI-compatible LLM request failed.") from exc

        answer = response.choices[0].message.content

        if not answer:
            return NO_ANSWER_TEXT

        logger.info(
            "LLM answer generated | provider=%s | model=%s",
            self.provider,
            self.model,
        )

        return answer.strip()

    def _extract_question_from_prompt(self, prompt: str) -> str:
        """
        Extract user question from either the current UTF-8 prompt or older
        mojibake prompt markers.
        """
        markers = [
            "\u3010\u7528\u6237\u95ee\u9898\u3011",
            "\u7528\u6237\u95ee\u9898\uff1a",
            "User question:",
            "Question:",
        ]

        for marker in markers:
            if marker in prompt:
                question_part = prompt.split(marker, 1)[1]
                for end_marker in [
                    "\u8bf7\u6839\u636e",
                    "Return JSON",
                    "Output JSON",
                ]:
                    if end_marker in question_part:
                        question_part = question_part.split(end_marker, 1)[0]
                return question_part.strip()

        return ""

    def _looks_like_router_prompt(self, prompt: str) -> bool:
        return "document_qa" in prompt and "general_chat" in prompt and "intent" in prompt

    def _generate_router_json_mock(self, text: str) -> str:
        lowered = text.lower()

        if self._contains_any(lowered, ["\u603b\u7ed3", "\u6982\u62ec", "\u63d0\u70bc", "summarize", "summary"]):
            intent = "summary"
            reason = "mock router: summary keyword"
        elif self._contains_any(lowered, ["\u5199", "\u6539\u5199", "\u6da6\u8272", "\u90ae\u4ef6", "write", "email", "draft"]):
            intent = "writing"
            reason = "mock router: writing keyword"
        elif self._contains_any(
            lowered,
            [
                "\u516c\u53f8",
                "\u6587\u6863",
                "\u653f\u7b56",
                "\u5236\u5ea6",
                "\u9000\u6b3e",
                "\u5ba2\u670d",
                "company",
                "policy",
                "document",
            ],
        ):
            intent = "document_qa"
            reason = "mock router: document keyword"
        else:
            intent = "general_chat"
            reason = "mock router: general question"

        return f'{{"intent": "{intent}", "reason": "{reason}"}}'

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)
