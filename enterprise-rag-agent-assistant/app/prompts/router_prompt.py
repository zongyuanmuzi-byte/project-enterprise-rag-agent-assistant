ALLOWED_INTENTS = {
    "document_qa",
    "summary",
    "writing",
    "general_chat",
}


def build_router_prompt(question: str) -> str:
    """
    Build a prompt that asks the LLM to classify user intent.

    The LLM must return JSON only.
    """
    return f"""
You are the intent router for an Enterprise RAG Agent Assistant.

Return JSON only. Do not return markdown. Do not explain outside JSON.

Allowed intents:
1. document_qa
- User asks about enterprise internal facts, company policies, business rules,
  procedures, document content, contract clauses, refund policy, customer
  service response time, people information, or anything that may exist in the
  uploaded knowledge base.
- Even if the answer may not exist in the knowledge base, route it to
  document_qa first. RAG will decide whether there is enough context.

2. summary
- Only when the user explicitly asks to summarize, condense, or extract key
  points from a provided text.

3. writing
- User asks to write, rewrite, polish, draft an email, notice, explanation, or
  other business text.

4. general_chat
- General concept explanation, casual chat, or non-enterprise-internal factual
  questions. Examples: what is RAG, what is FastAPI, how to understand embedding.

Output format:
{{
  "intent": "document_qa",
  "reason": "The user asks about information that may exist in enterprise documents."
}}

User question:
{question}
""".strip()
