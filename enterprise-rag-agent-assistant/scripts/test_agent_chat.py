import requests


BASE_URL = "http://127.0.0.1:8000"


TEST_CASES = [
    {
        "name": "document_qa",
        "payload": {
            "question": "公司的退款周期是多久？",
            "top_k": 3,
        },
    },
    {
        "name": "summary",
        "payload": {
            "question": "请总结一下这段内容：公司退款流程包括客服初步审核和财务部门审核。如果退款申请符合公司政策，财务部门会在审核通过后的 7 个工作日内完成退款处理。",
        },
    },
    {
        "name": "writing",
        "payload": {
            "question": "帮我写一封邮件，通知客户我们已经收到退款申请，会尽快完成审核。",
        },
    },
    {
        "name": "general_chat",
        "payload": {
            "question": "你好，你可以做什么？",
        },
    },
    {
        "name": "summary_too_short",
        "payload": {
            "question": "请总结：你好",
        },
    },
]


def call_agent_chat(payload: dict) -> dict:
    response = requests.post(
        f"{BASE_URL}/agent/chat",
        json=payload,
        timeout=30,
    )

    print("status_code:", response.status_code)

    try:
        return response.json()
    except Exception:
        return {
            "error": response.text,
        }


def main() -> None:
    for case in TEST_CASES:
        print("\n" + "=" * 80)
        print("TEST CASE:", case["name"])
        print("payload:", case["payload"])

        result = call_agent_chat(case["payload"])

        print("intent:", result.get("intent"))
        print("tool_used:", result.get("tool_used"))
        print("answer:", result.get("answer"))
        print("sources_count:", len(result.get("sources", [])))
        print("request_id:", result.get("request_id"))
        print("latency_ms:", result.get("latency_ms"))
        print("error:", result.get("error"))


if __name__ == "__main__":
    main()