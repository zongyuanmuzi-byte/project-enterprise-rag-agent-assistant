import json
import re
from typing import Any

from app.prompts.router_prompt import ALLOWED_INTENTS, build_router_prompt
from app.services.llm_service import LLMClient
from app.utils.logger import get_logger


logger = get_logger(__name__)


class AgentRouter:
    """
    Mainline Agent router.

    Strategy:
    1. Clear rules first.
    2. LLM intent classification.
    3. Rule fallback.
    """

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def route(self, question: str) -> dict[str, str]:
        cleaned_question = question.strip() if question else ""

        if not cleaned_question:
            raise ValueError("question cannot be empty.")

        rule_result = self._route_by_clear_rules(cleaned_question)

        if rule_result is not None:
            return rule_result

        prompt = build_router_prompt(cleaned_question)

        try:
            raw_output = self.llm_client.generate_answer(prompt)
            parsed = self._parse_router_output(raw_output)

            intent = parsed.get("intent")
            reason = parsed.get("reason", "")

            if intent not in ALLOWED_INTENTS:
                logger.warning(
                    "Router returned invalid intent | intent=%s | raw_output=%s",
                    intent,
                    raw_output,
                )
                return self._fallback_route(cleaned_question)

            return {
                "intent": intent,
                "reason": reason,
            }

        except Exception as exc:
            logger.warning(
                "LLM router failed, using fallback route | error_message=%s",
                str(exc),
            )
            return self._fallback_route(cleaned_question)

    def _parse_router_output(self, raw_output: str) -> dict[str, Any]:
        """
        Parse LLM JSON output.
        """
        if not raw_output or not raw_output.strip():
            raise ValueError("Router LLM returned empty output.")

        cleaned = raw_output.strip()
        cleaned = re.sub(r"^```json", "", cleaned)
        cleaned = re.sub(r"^```", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned)
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    def _route_by_clear_rules(self, question: str) -> dict[str, str] | None:
        q = question.strip().lower()

        if self._is_summary_request(q):
            return {
                "intent": "summary",
                "reason": "Clear rule: user explicitly asks to summarize provided text.",
            }

        if self._is_writing_request(q):
            return {
                "intent": "writing",
                "reason": "Clear rule: user asks for writing or rewriting.",
            }

        if self._is_document_qa_request(q):
            return {
                "intent": "document_qa",
                "reason": "Clear rule: user asks about enterprise or document facts.",
            }

        if self._is_general_concept_request(q):
            return {
                "intent": "general_chat",
                "reason": "Clear rule: user asks for a general concept explanation.",
            }

        return None

    def _fallback_route(self, question: str) -> dict[str, str]:
        rule_result = self._route_by_clear_rules(question)

        if rule_result is not None:
            rule_result["reason"] = f"Fallback {rule_result['reason'][0].lower()}{rule_result['reason'][1:]}"
            return rule_result

        return {
            "intent": "general_chat",
            "reason": "Rule fallback: no specialized task detected.",
        }

    def _is_summary_request(self, q: str) -> bool:
        summary_verbs = [
            "\u603b\u7ed3",
            "\u6982\u62ec",
            "\u6458\u8981",
            "\u63d0\u70bc",
            "\u5f52\u7eb3",
            "summarize",
            "summary",
        ]
        provided_text_markers = [
            "\u4e0b\u9762",
            "\u4ee5\u4e0b",
            "\u8fd9\u6bb5",
            "\u8fd9\u6bb5\u8bdd",
            "\u5185\u5bb9",
            "\u6587\u5b57",
            ":",
            "\uff1a",
        ]

        return self._contains_any(q, summary_verbs) and self._contains_any(q, provided_text_markers)

    def _is_writing_request(self, q: str) -> bool:
        writing_keywords = [
            "\u5e2e\u6211\u5199",
            "\u5199\u4e00",
            "\u5199\u5c01",
            "\u6539\u5199",
            "\u6da6\u8272",
            "\u751f\u6210\u90ae\u4ef6",
            "\u82f1\u6587\u90ae\u4ef6",
            "\u90ae\u4ef6",
            "\u901a\u77e5",
            "\u8bf4\u660e\u6587",
            "write",
            "rewrite",
            "polish",
            "draft",
            "email",
        ]

        return self._contains_any(q, writing_keywords)

    def _is_document_qa_request(self, q: str) -> bool:
        document_keywords = [
            "\u516c\u53f8",
            "\u4f01\u4e1a",
            "\u5185\u90e8",
            "\u77e5\u8bc6\u5e93",
            "\u6587\u6863",
            "\u8d44\u6599",
            "\u5236\u5ea6",
            "\u6d41\u7a0b",
            "\u653f\u7b56",
            "\u5408\u540c",
            "\u6761\u6b3e",
            "\u9000\u6b3e",
            "\u5ba2\u670d",
            "\u54cd\u5e94\u65f6\u95f4",
            "\u5458\u5de5",
            "\u8bf7\u5047",
            "\u53d1\u7968",
            "\u6570\u636e\u5b89\u5168",
            "\u5ba2\u6237\u4fe1\u606f",
            "ceo",
            "company",
            "policy",
            "document",
            "contract",
            "refund",
            "customer service",
        ]

        return self._contains_any(q, document_keywords)

    def _is_general_concept_request(self, q: str) -> bool:
        concept_patterns = [
            "\u4ec0\u4e48\u662f rag",
            "\u4ec0\u4e48\u662ffastapi",
            "fastapi \u662f\u4ec0\u4e48",
            "rag \u662f\u4ec0\u4e48",
            "what is rag",
            "what is fastapi",
            "\u600e\u4e48\u7406\u89e3",
            "\u8bf7\u7528\u7b80\u5355\u7684\u8bdd\u89e3\u91ca",
        ]

        return self._contains_any(q, concept_patterns)

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)
