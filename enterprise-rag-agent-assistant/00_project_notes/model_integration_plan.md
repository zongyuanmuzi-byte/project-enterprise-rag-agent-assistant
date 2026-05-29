# Enterprise RAG Agent Assistant 模型接入与 Router 优化说明

生成日期：2026-05-28

## 1. 本次接入真实 LLM / Embedding 的目标

本阶段目标是在不重写 RAGService、不改数据库表结构、不引入新框架的前提下，让项目同时支持：

- 本地 mock LLM / mock embedding，用于无 API key 的稳定开发和测试。
- OpenAI-compatible LLM / embedding，用于接入真实模型服务。
- 更稳定的 Agent Router intent 分类，避免企业知识库问题被误判成 summary 或 general_chat。

## 2. 需要的 .env 配置项

```env
LOG_LEVEL=INFO

DATABASE_URL=sqlite:///./data/app.db

CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=3
MIN_RELEVANCE_SCORE=0.2

CHROMA_PATH=data/chroma_db
CHROMA_COLLECTION_NAME=enterprise_knowledge_base

EMBEDDING_PROVIDER=mock
EMBEDDING_MODEL=mock-embedding
EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_BASE_URL=https://your-openai-compatible-embedding-endpoint/v1
EMBEDDING_TIMEOUT_SECONDS=30

LLM_PROVIDER=mock
LLM_MODEL=mock-llm
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://your-openai-compatible-llm-endpoint/v1
LLM_TIMEOUT_SECONDS=60
```

兼容说明：

- `TOP_K` 是推荐配置名。
- 旧的 `DEFAULT_TOP_K` 仍可被读取。
- `CHROMA_PATH` 是推荐配置名。
- 旧的 `CHROMA_PERSIST_DIR` 仍可被读取。

## 3. mock 和 openai_compatible 的区别

mock 模式：

- 不调用外部模型。
- 不需要 API key。
- embedding 是确定性的伪向量，只用于工程链路验证。
- LLM 是本地 mock 输出，只用于确认 API、RAG、Agent 调用链路是否跑通。
- 适合本地开发、CI、Router 单元测试。

openai_compatible 模式：

- 使用 OpenAI-compatible API。
- `LLM_PROVIDER=openai_compatible` 时调用 chat completions。
- `EMBEDDING_PROVIDER=openai_compatible` 时调用 embeddings API。
- 需要填写对应 `BASE_URL`、`API_KEY`、`MODEL`。
- 代码不会把 API key 输出到日志。

## 4. 切换 embedding 后为什么要清空 Chroma 并重新入库

不同 embedding 模型生成的向量不在同一个向量空间里。

如果先用 mock embedding 入库，再切换到真实 embedding 提问，query 向量和已存 chunk 向量不是同一套坐标体系，检索结果会失真。

因此只要切换以下任意配置：

- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_BASE_URL` 指向的实际 embedding 模型

就必须清空：

```text
data/chroma_db
data/app.db
```

然后重新通过 `/documents/upload` 上传文档入库。

## 5. Router 三层策略

当前 `app/agent/router.py` 采用三层策略：

```text
1. 明确规则优先
2. LLM intent 分类
3. 规则 fallback
```

这样做的原因：

- 明显的文档问答、总结、写作、通用概念问题，不需要消耗 LLM Router。
- 模糊问题再交给 LLM 分类。
- LLM 输出非法 JSON、intent 不合法、调用失败时，系统仍能 fallback 到规则。

LLM Router 必须输出：

```json
{
  "intent": "document_qa",
  "reason": "The user asks about information that may exist in enterprise documents."
}
```

允许的 intent 只有：

- `document_qa`
- `summary`
- `writing`
- `general_chat`

## 6. intent 分类边界

`document_qa`：

- 企业内部事实、公司政策、制度流程、文档资料、合同条款、退款政策、客服响应、人物信息、知识库中可能存在的信息。
- 即使知识库没有答案，也应该先走 `document_qa`，由 RAG 返回资料不足。
- 例子：公司的退款周期是多久？公司 CEO 的生日是哪天？客服响应时间是多久？

`summary`：

- 只有用户明确要求总结、概括、提炼某段内容时才是 summary。
- 例子：请总结下面这段话：……

`writing`：

- 用户要求写作、改写、润色、生成邮件、通知、说明文。
- 例子：帮我写一封英文邮件，告诉客户我们已经收到退款申请。

`general_chat`：

- 普通概念解释、闲聊、非企业内部事实查询。
- 例子：什么是 RAG？FastAPI 是什么？embedding 怎么理解？

## 7. 如何测试 /chat

1. 启动服务：

```bash
uvicorn app.main:app --reload
```

2. 上传文档：

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -F "file=@data/sample_docs/company_policy.md"
```

3. 提问：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司的退款周期是多久？\"}"
```

预期返回：

- `answer`
- `sources`
- `request_id`
- `latency_ms`

## 8. 如何测试 /agent/chat

```bash
curl -X POST "http://127.0.0.1:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司的退款周期是多久？\"}"
```

预期：

- Router 将该问题判断为 `document_qa`
- ToolExecutor 调用 `rag_tool`
- `rag_tool` 调用 `RAGService`
- 返回 `answer + sources`

Router 单元测试：

```bash
pytest tests/test_agent_router.py
```

这组测试在 mock LLM 模式下稳定运行，不依赖真实 API key。
