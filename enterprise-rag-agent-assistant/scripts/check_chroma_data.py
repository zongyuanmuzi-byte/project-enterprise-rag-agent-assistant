from app.services.vector_store_service import VectorStoreService


def main() -> None:
    vector_store = VectorStoreService()

    print("chroma collection count:", vector_store.count())


if __name__ == "__main__":
    main()