import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_app.db"
os.environ["CHROMA_PATH"] = "data/test_chroma_db"

from app.agent.router import AgentRouter
from app.config import settings


def test_agent_router_intents_in_mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_model", "mock-llm")
    monkeypatch.setattr(settings, "llm_api_key", "")
    monkeypatch.setattr(settings, "llm_base_url", "")

    router = AgentRouter()

    cases = [
        ("\u516c\u53f8\u7684\u9000\u6b3e\u5468\u671f\u662f\u591a\u4e45\uff1f", "document_qa"),
        ("\u516c\u53f8 CEO \u7684\u751f\u65e5\u662f\u54ea\u5929\uff1f", "document_qa"),
        (
            "\u8bf7\u603b\u7ed3\u4e0b\u9762\u8fd9\u6bb5\u8bdd\uff1a"
            "\u5ba2\u6237\u9000\u6b3e\u9700\u8981\u5148\u5ba1\u6838\uff0c"
            "\u518d\u7531\u8d22\u52a1\u5904\u7406\u3002",
            "summary",
        ),
        (
            "\u5e2e\u6211\u5199\u4e00\u5c01\u82f1\u6587\u90ae\u4ef6\uff0c"
            "\u544a\u8bc9\u5ba2\u6237\u6211\u4eec\u5df2\u7ecf\u6536\u5230\u9000\u6b3e\u7533\u8bf7\u3002",
            "writing",
        ),
        ("\u8bf7\u7528\u7b80\u5355\u7684\u8bdd\u89e3\u91ca\u4ec0\u4e48\u662f RAG\u3002", "general_chat"),
    ]

    for question, expected_intent in cases:
        result = router.route(question)
        assert result["intent"] == expected_intent
