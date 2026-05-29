from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        description="User question for the RAG assistant.",
        examples=["公司的退款周期是多久？"],
    )
    top_k: int | None = Field(
        default=None,
        description="Number of retrieved chunks to use.",
        examples=[3],
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("question cannot be empty.")

        return cleaned_value

    @field_validator("top_k")
    @classmethod
    def top_k_must_be_positive(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("top_k must be greater than 0.")

        return value
    

class SourceItem(BaseModel):
    filename: str | None = Field(
        default=None,
        description="Source filename.",
        examples=["company_policy.md"],
    )
    chunk_index: int | None = Field(
        default=None,
        description="Chunk index in the source document.",
        examples=[0],
    )
    document_id: int | None = Field(
        default=None,
        description="Source document ID.",
        examples=[1],
    )
    content: str = Field(
        ...,
        description="Retrieved source content.",
        examples=["财务部门会在审核通过后的 7 个工作日内完成退款处理。"],
    )
    distance: float | None = Field(
        default=None,
        description="Vector distance returned by Chroma. Smaller usually means more similar.",
        examples=[0.23],
    )
    relevance_score: float | None = Field(
        default=None,
        description="Normalized relevance score derived from Chroma distance. Larger means more relevant.",
        examples=[0.81],
    )



class ChatResponse(BaseModel):
    answer: str = Field(
        ...,
        description="Assistant answer.",
        examples=["退款会在审核通过后的 7 个工作日内完成，特殊情况可能额外需要 3 到 5 个工作日。"],
    )
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="Retrieved sources used for the answer.",
    )
    request_id: str = Field(
        ...,
        description="Unique request ID for tracing this chat request.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    latency_ms: int = Field(
        ...,
        description="Request latency in milliseconds.",
        examples=[123],
    )

class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="Human-readable error message.",
        examples=["question cannot be empty."],
    )
    request_id: str | None = Field(
        default=None,
        description="Request ID if available.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
class DocumentIndexRequest(BaseModel):
    file_path: str = Field(
        ...,
        description="Path of the document to index.",
        examples=["data/sample_docs/company_policy.md"],
    )

    @field_validator("file_path")
    @classmethod
    def file_path_must_not_be_empty(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("file_path cannot be empty.")

        return cleaned_value


class DocumentIndexResponse(BaseModel):
    document_id: int = Field(
        ...,
        description="ID of the indexed document.",
        examples=[1],
    )
    filename: str = Field(
        ...,
        description="Indexed filename.",
        examples=["company_policy.md"],
    )
    chunks_count: int = Field(
        ...,
        description="Number of chunks generated from this document.",
        examples=[3],
    )
    status: str = Field(
        ...,
        description="Indexing status.",
        examples=["indexed_to_sql"],
    )

class AgentChatRequest(BaseModel):
    question: str = Field(
        ...,
        description="User question or instruction for the Agent assistant.",
        examples=["请总结一下这段内容：公司退款流程包括初审和财务审核。"],
    )
    top_k: int | None = Field(
        default=None,
        description="Number of retrieved chunks when using rag_tool.",
        examples=[3],
    )

    @field_validator("question")
    @classmethod
    def agent_question_must_not_be_empty(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("question cannot be empty.")

        return cleaned_value

    @field_validator("top_k")
    @classmethod
    def agent_top_k_must_be_positive(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("top_k must be greater than 0.")

        return value


class AgentChatResponse(BaseModel):
    intent: str = Field(
        ...,
        description="Detected user intent.",
        examples=["summary"],
    )
    tool_used: str = Field(
        ...,
        description="Tool used by the Agent.",
        examples=["summary_tool"],
    )
    answer: str = Field(
        ...,
        description="Final answer generated by the selected tool.",
    )
    sources: list[SourceItem] = Field(
        default_factory=list,
        description="Sources returned by rag_tool. Empty for non-RAG tools.",
    )
    request_id: str = Field(
        ...,
        description="Unique request ID for tracing.",
    )
    latency_ms: int = Field(
        ...,
        description="Request latency in milliseconds.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the Agent flow failed.",
    )


class FeedbackRequest(BaseModel):
    chat_log_id: int = Field(
        ...,
        description="ID of the chat log being rated.",
        examples=[1],
    )
    rating: int = Field(
        ...,
        description="User rating from 1 to 5.",
        examples=[4],
    )
    comment: str | None = Field(
        default=None,
        description="Optional user feedback comment.",
        examples=["The answer cited the correct policy."],
    )

    @field_validator("chat_log_id")
    @classmethod
    def chat_log_id_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("chat_log_id must be greater than 0.")

        return value

    @field_validator("rating")
    @classmethod
    def rating_must_be_between_1_and_5(cls, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("rating must be between 1 and 5.")

        return value


class FeedbackResponse(BaseModel):
    feedback_id: int = Field(
        ...,
        description="ID of the created feedback item.",
        examples=[1],
    )
    chat_log_id: int = Field(
        ...,
        description="ID of the rated chat log.",
        examples=[1],
    )
    rating: int = Field(
        ...,
        description="User rating from 1 to 5.",
        examples=[4],
    )
    comment: str | None = Field(
        default=None,
        description="Optional user feedback comment.",
        examples=["The answer cited the correct policy."],
    )
    status: str = Field(
        ...,
        description="Feedback creation status.",
        examples=["created"],
    )
