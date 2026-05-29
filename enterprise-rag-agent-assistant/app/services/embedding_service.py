import hashlib
import random
from typing import Literal

from app.config import settings
from app.utils.logger import get_logger


logger = get_logger(__name__)


EmbeddingProvider = Literal["mock", "openai_compatible"]


class EmbeddingClient:
    """
    Unified embedding client.

    Important:
    If you switch EMBEDDING_MODEL or EMBEDDING_PROVIDER, clear data/chroma_db
    and data/app.db, then upload documents again. Old vectors and new vectors
    are not in the same embedding space.
    """

    def __init__(self) -> None:
        self.provider: EmbeddingProvider = settings.embedding_provider  # type: ignore
        self.model = settings.embedding_model
        self.api_key = settings.embedding_api_key
        self.base_url = settings.embedding_base_url
        self.timeout_seconds = settings.embedding_timeout_seconds

        self.mock_embedding_dim = 384

        if self.provider == "openai_compatible":
            if not self.api_key:
                raise ValueError(
                    "EMBEDDING_API_KEY is required when EMBEDDING_PROVIDER=openai_compatible."
                )

            from openai import OpenAI

            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout_seconds,
            }

            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            self.client = OpenAI(**client_kwargs)
        else:
            self.client = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Convert a list of strings into embedding vectors.
        """
        if not texts:
            raise ValueError("texts cannot be empty.")

        cleaned_texts = [text.strip() for text in texts if text and text.strip()]

        if not cleaned_texts:
            raise ValueError("texts cannot contain only empty strings.")

        try:
            if self.provider == "mock":
                return self._embed_texts_mock(cleaned_texts)

            if self.provider == "openai_compatible":
                return self._embed_texts_openai_compatible(cleaned_texts)

            raise ValueError(f"Unsupported embedding provider: {self.provider}")

        except Exception as exc:
            logger.exception(
                "Embedding failed | provider=%s | model=%s | texts_count=%s | error_type=%s",
                self.provider,
                self.model,
                len(cleaned_texts),
                type(exc).__name__,
            )
            raise RuntimeError("Embedding generation failed.") from exc

    def _embed_texts_mock(self, texts: list[str]) -> list[list[float]]:
        """
        Generate deterministic fake embeddings for local development.
        """
        embeddings: list[list[float]] = []

        for text in texts:
            seed = self._text_to_seed(text)
            random_generator = random.Random(seed)

            vector = [
                random_generator.uniform(-1.0, 1.0)
                for _ in range(self.mock_embedding_dim)
            ]

            embeddings.append(vector)

        logger.info(
            "Mock embeddings generated | texts_count=%s | dim=%s",
            len(texts),
            self.mock_embedding_dim,
        )

        return embeddings

    def _embed_texts_openai_compatible(self, texts: list[str]) -> list[list[float]]:
        """
        Call an OpenAI-compatible embeddings API.
        """
        if self.client is None:
            raise RuntimeError("OpenAI-compatible embedding client is not initialized.")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
        except Exception as exc:
            logger.exception(
                "OpenAI-compatible embedding request failed | provider=%s | model=%s | texts_count=%s | error_type=%s",
                self.provider,
                self.model,
                len(texts),
                type(exc).__name__,
            )
            raise RuntimeError("OpenAI-compatible embedding request failed.") from exc

        embeddings = [item.embedding for item in response.data]

        if len(embeddings) != len(texts):
            raise RuntimeError(
                f"Embedding response count mismatch: expected={len(texts)}, got={len(embeddings)}"
            )

        logger.info(
            "Embeddings generated | provider=%s | model=%s | texts_count=%s",
            self.provider,
            self.model,
            len(texts),
        )

        return embeddings

    @staticmethod
    def _text_to_seed(text: str) -> int:
        """
        Convert text to a stable integer seed using md5.
        """
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)
