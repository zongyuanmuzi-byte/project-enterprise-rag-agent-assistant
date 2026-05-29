from app.utils.logger import get_logger


logger = get_logger(__name__)


NO_ANSWER_TEXT = "知识库中没有找到明确答案。"


RAG_SYSTEM_INSTRUCTION = """
你是一个企业知识库问答助手。

你的任务是根据给定的企业知识库资料回答用户问题。

请严格遵守以下规则：
1. 只能根据【资料】中的内容回答。
2. 如果【资料】中没有明确答案，请回答：“知识库中没有找到明确答案。”
3. 不要编造资料中不存在的信息。
4. 不要使用你自己的外部知识补充答案。
5. 回答要简洁、清晰、直接。
6. 如果资料中包含多个相关信息，请合并后回答。
7. 不需要在回答正文中编造来源编号，具体 sources 会由程序单独返回。
""".strip()


def build_rag_prompt(context: str, question: str) -> str:
    """
    Build the final RAG prompt for the LLM.

    Args:
        context: Retrieved document chunks joined as context.
        question: User question.

    Returns:
        A complete prompt string.
    """
    cleaned_context = context.strip() if context else ""
    cleaned_question = question.strip() if question else ""

    if not cleaned_question:
        raise ValueError("question cannot be empty when building RAG prompt.")

    if not cleaned_context:
        logger.warning("Empty context when building RAG prompt.")

    prompt = f"""
{RAG_SYSTEM_INSTRUCTION}

【资料】
{cleaned_context}

【用户问题】
{cleaned_question}

请根据【资料】回答用户问题：
""".strip()

    return prompt


def build_context_from_chunks(chunks: list[dict]) -> str:
    """
    Build context text from retrieved chunks.

    Args:
        chunks:
            [
                {
                    "content": "...",
                    "filename": "company_policy.md",
                    "chunk_index": 0,
                    "distance": 0.23
                }
            ]

    Returns:
        A joined context string.
    """
    if not chunks:
        return ""

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        filename = chunk.get("filename", "unknown")
        chunk_index = chunk.get("chunk_index", "unknown")
        content = chunk.get("content", "").strip()

        if not content:
            continue

        context_parts.append(
            f"【资料片段 {index}】\n"
            f"来源文件：{filename}\n"
            f"chunk_index：{chunk_index}\n"
            f"内容：\n{content}"
        )

    return "\n\n".join(context_parts)