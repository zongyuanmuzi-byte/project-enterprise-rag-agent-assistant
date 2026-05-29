from app.services.embedding_service import EmbeddingClient
from app.services.vector_store_service import VectorStoreService


def main() -> None:
    chunks = [
        {
            "content": "客户提交退款申请后，客服团队会在 2 个工作日内完成初步审核。财务部门会在审核通过后的 7 个工作日内完成退款处理。",
            "chunk_index": 0,
            "metadata": {
                "document_id": 999,
                "filename": "test_policy.md",
                "chunk_index": 0,
            },
        },
        {
            "content": "员工每周最多可以申请 2 天远程办公。远程办公需要提前一天向直属主管申请。",
            "chunk_index": 1,
            "metadata": {
                "document_id": 999,
                "filename": "test_policy.md",
                "chunk_index": 1,
            },
        },
    ]

    embedding_client = EmbeddingClient()
    vector_store = VectorStoreService()

    texts = [chunk["content"] for chunk in chunks]
    embeddings = embedding_client.embed_texts(texts)

    add_result = vector_store.add_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print("add result:")
    print(add_result)

    question = "公司的退款多久能到账？"
    query_embedding = embedding_client.embed_texts([question])[0]

    search_results = vector_store.search_similar_chunks(
        query_embedding=query_embedding,
        top_k=2,
    )

    print("\nsearch results:")
    for item in search_results:
        print(item)


if __name__ == "__main__":
    main()