from app.services.embedding_service import EmbeddingClient


def main() -> None:
    client = EmbeddingClient()

    texts = [
        "客户提交退款申请后，客服团队会在 2 个工作日内完成初步审核。",
        "员工每周最多可以申请 2 天远程办公。",
    ]

    embeddings = client.embed_texts(texts)

    print("embeddings count:", len(embeddings))
    print("first embedding dim:", len(embeddings[0]))
    print("second embedding dim:", len(embeddings[1]))
    print("first embedding preview:", embeddings[0][:5])


if __name__ == "__main__":
    main()