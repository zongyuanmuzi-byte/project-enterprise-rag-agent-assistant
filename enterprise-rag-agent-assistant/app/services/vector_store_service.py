from typing import Any

import chromadb

from app.config import settings
from app.utils.logger import get_logger


logger = get_logger(__name__)


class VectorStoreService:
    """
    Provider facade for vector store implementations.

    The default provider is Chroma for local development. Tencent VectorDB is
    prepared as a production-mode adapter boundary and intentionally raises a
    clear error until the official SDK/API integration is completed.
    """

    def __init__(self) -> None:
        provider = settings.vector_store_provider.lower().strip()

        if provider == "chroma":
            self.backend = ChromaVectorStoreService()
        elif provider == "tencent_vectordb":
            self.backend = TencentVectorDBStore()
        else:
            raise ValueError(f"Unsupported vector store provider: {settings.vector_store_provider}")

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> dict[str, Any]:
        return self.backend.add_chunks(chunks=chunks, embeddings=embeddings)

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        return self.backend.search_similar_chunks(
            query_embedding=query_embedding,
            top_k=top_k,
        )

    def count(self) -> int:
        return self.backend.count()


class ChromaVectorStoreService:
    """
    Chroma vector store service.

    Responsibilities:
    1. Initialize persistent Chroma client.
    2. Create or get collection.
    3. Add chunk embeddings.
    4. Search similar chunks by query embedding.
    """

    def __init__(self) -> None:
        self.persist_dir = settings.chroma_persist_dir
        self.collection_name = settings.chroma_collection_name

        self.client = chromadb.PersistentClient(path=self.persist_dir)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Enterprise knowledge base chunks for RAG",
            },
        )

        logger.info(
            "Chroma vector store initialized | persist_dir=%s | collection=%s",
            self.persist_dir,
            self.collection_name,
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> dict[str, Any]:
        """
        Add chunks and their embeddings into Chroma.

        Args:
            chunks:
                [
                    {
                        "content": "...",
                        "chunk_index": 0,
                        "metadata": {
                            "document_id": 1,
                            "filename": "company_policy.md",
                            "chunk_index": 0
                        }
                    }
                ]

            embeddings:
                [
                    [0.1, 0.2, ...],
                    [0.3, 0.4, ...]
                ]

        Returns:
            {
                "added_count": 3,
                "collection_name": "enterprise_knowledge_base"
            }
        """
        if not chunks:
            raise ValueError("chunks cannot be empty.")

        if not embeddings:
            raise ValueError("embeddings cannot be empty.")

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"chunks and embeddings length mismatch: "
                f"chunks={len(chunks)}, embeddings={len(embeddings)}"
            )

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            metadata = chunk.get("metadata", {})

            document_id = metadata.get("document_id")
            filename = metadata.get("filename")
            chunk_index = metadata.get("chunk_index")

            if document_id is None or filename is None or chunk_index is None:
                raise ValueError(
                    "Each chunk metadata must contain document_id, filename, and chunk_index."
                )

            chunk_id = f"doc_{document_id}_chunk_{chunk_index}"

            ids.append(chunk_id)
            documents.append(chunk["content"])
            metadatas.append(
                {
                    "document_id": int(document_id),
                    "filename": str(filename),
                    "chunk_index": int(chunk_index),
                }
            )

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(
            "Chunks added to Chroma | collection=%s | added_count=%s",
            self.collection_name,
            len(chunks),
        )

        return {
            "added_count": len(chunks),
            "collection_name": self.collection_name,
        }

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search similar chunks by query embedding.

        Args:
            query_embedding: Embedding vector of the user question.
            top_k: Number of results to return.

        Returns:
            [
                {
                    "content": "...",
                    "filename": "company_policy.md",
                    "chunk_index": 0,
                    "document_id": 1,
                    "distance": 0.23,
                    "relevance_score": 0.81
                }
            ]

        Chroma returns distance, where smaller means more similar. This service
        also exposes relevance_score, where larger means more relevant, to make
        downstream filtering easier to reason about.
        """
        if top_k is None:
            top_k = settings.default_top_k

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        if not query_embedding:
            raise ValueError("query_embedding cannot be empty.")

        collection_count = self.collection.count()

        if collection_count == 0:
            raise ValueError("Vector store is empty. Please index documents first.")

        n_results = min(top_k, collection_count)

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        search_results: list[dict[str, Any]] = []

        for content, metadata, distance in zip(documents, metadatas, distances):
            search_results.append(
                {
                    "content": content,
                    "filename": metadata.get("filename"),
                    "chunk_index": metadata.get("chunk_index"),
                    "document_id": metadata.get("document_id"),
                    "distance": distance,
                    "relevance_score": self._distance_to_relevance_score(distance),
                }
            )

        logger.info(
            "Chroma search completed | collection=%s | top_k=%s | returned=%s",
            self.collection_name,
            top_k,
            len(search_results),
        )

        return search_results

    def count(self) -> int:
        """
        Return number of records in the Chroma collection.
        """
        return self.collection.count()

    @staticmethod
    def _distance_to_relevance_score(distance: float | int | None) -> float:
        """
        Convert Chroma distance to a normalized relevance score.

        Chroma distance: smaller is more relevant.
        relevance_score: larger is more relevant, in the range (0, 1].
        """
        if distance is None:
            return 0.0

        distance_value = float(distance)

        if distance_value < 0:
            distance_value = 0.0

        return 1.0 / (1.0 + distance_value)


class TencentVectorDBStore:
    """
    Tencent VectorDB adapter placeholder.

    This class defines the provider boundary needed to replace local Chroma in
    Tencent Cloud mode. The exact SDK/client calls should be completed against
    the Tencent VectorDB official Python SDK/API for the selected instance type.
    """

    def __init__(self) -> None:
        self.url = settings.tencent_vectordb_url
        self.database = settings.tencent_vectordb_database
        self.collection = settings.tencent_vectordb_collection
        self.dimension = settings.tencent_vectordb_dimension

        logger.info(
            "Tencent VectorDB provider selected | url=%s | database=%s | collection=%s | dimension=%s",
            self.url,
            self.database,
            self.collection,
            self.dimension,
        )

        raise NotImplementedError(
            "VECTOR_STORE_PROVIDER=tencent_vectordb is prepared but not fully implemented. "
            "Please complete Tencent VectorDB SDK/API integration before enabling it."
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> dict[str, Any]:
        raise NotImplementedError("Tencent VectorDB add_chunks is not implemented yet.")

    def search_similar_chunks(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("Tencent VectorDB search_similar_chunks is not implemented yet.")

    def count(self) -> int:
        raise NotImplementedError("Tencent VectorDB count is not implemented yet.")
