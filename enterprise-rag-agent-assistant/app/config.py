from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # =========================
    # App
    # =========================
    app_name: str = "Enterprise RAG Agent Assistant"
    app_env: str = "development"
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    # =========================
    # Database
    # =========================
    database_url: str = Field(
        default="sqlite:///./data/app.db",
        validation_alias="DATABASE_URL",
    )

    # =========================
    # Storage
    # =========================
    storage_provider: str = Field(default="local", validation_alias="STORAGE_PROVIDER")
    upload_dir: str = Field(default="./data/uploads", validation_alias="UPLOAD_DIR")
    cos_secret_id: str = Field(default="", validation_alias="COS_SECRET_ID")
    cos_secret_key: str = Field(default="", validation_alias="COS_SECRET_KEY")
    cos_bucket: str = Field(default="", validation_alias="COS_BUCKET")
    cos_region: str = Field(default="", validation_alias="COS_REGION")
    cos_prefix: str = Field(default="uploads/", validation_alias="COS_PREFIX")

    # =========================
    # RAG - Text Split
    # =========================
    chunk_size: int = Field(default=800, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=120, validation_alias="CHUNK_OVERLAP")

    # =========================
    # RAG - Retrieval
    # =========================
    default_top_k: int = Field(
        default=3,
        validation_alias=AliasChoices("TOP_K", "DEFAULT_TOP_K"),
    )
    min_relevance_score: float = Field(
        default=0.2,
        validation_alias="MIN_RELEVANCE_SCORE",
    )

    # =========================
    # Chroma Vector Store
    # =========================
    chroma_persist_dir: str = Field(
        default="data/chroma_db",
        validation_alias=AliasChoices("CHROMA_PATH", "CHROMA_PERSIST_DIR"),
    )
    chroma_collection_name: str = Field(
        default="enterprise_knowledge_base",
        validation_alias="CHROMA_COLLECTION_NAME",
    )
    vector_store_provider: str = Field(default="chroma", validation_alias="VECTOR_STORE_PROVIDER")
    tencent_vectordb_url: str = Field(default="", validation_alias="TENCENT_VECTORDB_URL")
    tencent_vectordb_api_key: str = Field(default="", validation_alias="TENCENT_VECTORDB_API_KEY")
    tencent_vectordb_username: str = Field(default="", validation_alias="TENCENT_VECTORDB_USERNAME")
    tencent_vectordb_password: str = Field(default="", validation_alias="TENCENT_VECTORDB_PASSWORD")
    tencent_vectordb_database: str = Field(default="", validation_alias="TENCENT_VECTORDB_DATABASE")
    tencent_vectordb_collection: str = Field(
        default="enterprise_rag_chunks",
        validation_alias="TENCENT_VECTORDB_COLLECTION",
    )
    tencent_vectordb_dimension: int = Field(
        default=2048,
        validation_alias="TENCENT_VECTORDB_DIMENSION",
    )

    # =========================
    # Embedding
    # =========================
    embedding_provider: str = Field(default="mock", validation_alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="mock-embedding", validation_alias="EMBEDDING_MODEL")
    embedding_api_key: str = Field(default="", validation_alias="EMBEDDING_API_KEY")
    embedding_base_url: str = Field(default="", validation_alias="EMBEDDING_BASE_URL")
    embedding_timeout_seconds: float = Field(
        default=30.0,
        validation_alias="EMBEDDING_TIMEOUT_SECONDS",
    )

    # =========================
    # LLM
    # =========================
    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default="mock-llm", validation_alias="LLM_MODEL")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", validation_alias="LLM_BASE_URL")
    llm_timeout_seconds: float = Field(default=60.0, validation_alias="LLM_TIMEOUT_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()


def validate_settings() -> None:
    """
    Validate important settings at application startup.

    This is intentionally lightweight for the beginner-friendly stage.
    Later we can add stricter validation for production.
    """
    if settings.chunk_overlap >= settings.chunk_size:
        raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

    if settings.default_top_k <= 0:
        raise ValueError("TOP_K must be greater than 0.")

    cors_origins = settings.get_cors_origins()

    if not cors_origins:
        raise ValueError("CORS_ORIGINS cannot be empty.")

    if "*" in cors_origins:
        raise ValueError("CORS_ORIGINS cannot use '*'. Please set explicit origins.")

    if not settings.upload_dir.strip():
        raise ValueError("UPLOAD_DIR cannot be empty.")

    storage_provider = settings.storage_provider.lower().strip()

    if storage_provider not in ["local", "cos"]:
        raise ValueError("STORAGE_PROVIDER must be 'local' or 'cos'.")

    if storage_provider == "cos":
        missing_cos_fields = [
            name
            for name, value in {
                "COS_SECRET_ID": settings.cos_secret_id,
                "COS_SECRET_KEY": settings.cos_secret_key,
                "COS_BUCKET": settings.cos_bucket,
                "COS_REGION": settings.cos_region,
            }.items()
            if not value.strip()
        ]

        if missing_cos_fields:
            raise ValueError(
                "Missing required COS settings: " + ", ".join(missing_cos_fields)
            )

    if settings.min_relevance_score < 0:
        raise ValueError("MIN_RELEVANCE_SCORE cannot be negative.")

    vector_store_provider = settings.vector_store_provider.lower().strip()

    if vector_store_provider not in ["chroma", "tencent_vectordb"]:
        raise ValueError("VECTOR_STORE_PROVIDER must be 'chroma' or 'tencent_vectordb'.")

    if vector_store_provider == "tencent_vectordb":
        missing_vector_fields = [
            name
            for name, value in {
                "TENCENT_VECTORDB_URL": settings.tencent_vectordb_url,
                "TENCENT_VECTORDB_DATABASE": settings.tencent_vectordb_database,
                "TENCENT_VECTORDB_COLLECTION": settings.tencent_vectordb_collection,
            }.items()
            if not value.strip()
        ]

        if missing_vector_fields:
            raise ValueError(
                "Missing required Tencent VectorDB settings: "
                + ", ".join(missing_vector_fields)
            )

    if settings.tencent_vectordb_dimension <= 0:
        raise ValueError("TENCENT_VECTORDB_DIMENSION must be greater than 0.")

    if settings.embedding_timeout_seconds <= 0:
        raise ValueError("EMBEDDING_TIMEOUT_SECONDS must be greater than 0.")

    if settings.llm_timeout_seconds <= 0:
        raise ValueError("LLM_TIMEOUT_SECONDS must be greater than 0.")

    if settings.embedding_provider not in ["mock", "openai_compatible"]:
        raise ValueError("EMBEDDING_PROVIDER must be 'mock' or 'openai_compatible'.")

    if settings.llm_provider not in ["mock", "openai_compatible"]:
        raise ValueError("LLM_PROVIDER must be 'mock' or 'openai_compatible'.")
