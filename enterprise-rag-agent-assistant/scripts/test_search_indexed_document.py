from app.services.embedding_service import EmbeddingClient
from app.services.vector_store_service import VectorStoreService


def main() -> None:
    question = "公司的退款周期是多久？"

    embedding_client = EmbeddingClient()
    vector_store = VectorStoreService()

    query_embedding = embedding_client.embed_texts([question])[0]

    results = vector_store.search_similar_chunks(
        query_embedding=query_embedding,
        top_k=3,
    )

    print("question:", question)
    print("\n--- search results ---")

    for item in results:
        print("filename:", item["filename"])
        print("chunk_index:", item["chunk_index"])
        print("document_id:", item["document_id"])
        print("distance:", item["distance"])
        print("content preview:", item["content"][:200])
        print("-" * 50)


if __name__ == "__main__":
    main()