from app.database.db import SessionLocal
from app.services.langgraph_agent import LangGraphAgent


def main() -> None:
    db = SessionLocal()

    try:
        agent = LangGraphAgent()

        questions = [
            "公司的退款周期是多久？",
            "请总结一下这段内容：公司退款流程包括客服初步审核和财务部门审核，符合政策后会在 7 个工作日内完成退款处理。",
            "帮我写一封邮件，通知客户我们已经收到退款申请。",
            "你好，你可以做什么？",
        ]

        for question in questions:
            print("\n" + "=" * 80)
            print("question:", question)

            state = agent.run(
                question=question,
                db=db,
                top_k=3,
            )

            print("intent:", state.get("intent"))
            print("reason:", state.get("reason"))
            print("tool_used:", state.get("tool_used"))
            print("answer:", state.get("answer"))
            print("sources_count:", len(state.get("sources", [])))
            print("error:", state.get("error"))

    finally:
        db.close()


if __name__ == "__main__":
    main()