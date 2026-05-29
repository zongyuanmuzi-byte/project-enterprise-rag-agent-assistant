from app.database.db import SessionLocal
from app.database.models import ChatLog


def main() -> None:
    db = SessionLocal()

    try:
        logs = (
            db.query(ChatLog)
            .order_by(ChatLog.created_at.desc())
            .limit(10)
            .all()
        )

        for log in logs:
            print("-" * 80)
            print("request_id:", log.request_id)
            print("question:", log.question)
            print("answer:", log.answer)
            print("intent:", log.intent)
            print("tool_used:", log.tool_used)
            print("latency_ms:", log.latency_ms)
            print("error_message:", log.error_message)

    finally:
        db.close()


if __name__ == "__main__":
    main()