from app.database.db import SessionLocal, init_db
from app.services.document_service import index_document_to_sql


def main() -> None:
    init_db()

    db = SessionLocal()

    try:
        result = index_document_to_sql(
            file_path="data/sample_docs/company_policy.md",
            db=db,
        )

        print("index result:")
        print(result)

    finally:
        db.close()


if __name__ == "__main__":
    main()