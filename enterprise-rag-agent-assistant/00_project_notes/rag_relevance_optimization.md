# RAG 检索相关性过滤优化记录

生成日期：2026-05-28

## 1. 为什么需要 MIN_RELEVANCE_SCORE

RAG 问答不能把向量库返回的所有 chunks 都直接送给 LLM。

如果检索结果与用户问题相关性很低，LLM 可能会基于弱相关资料生成看似合理但没有依据的回答。`MIN_RELEVANCE_SCORE` 用于设置最低相关性门槛：

- 达到阈值的 chunks：允许进入 RAG context。
- 低于阈值的 chunks：过滤掉，不送入 LLM。
- 过滤后没有合格 chunks：直接返回 no-answer，不调用 LLM 生成具体答案。

## 2. distance / relevance_score 的含义

Chroma 查询结果返回 `distance`。

当前项目约定：

- `distance`：Chroma 原始距离，越小越相关。
- `relevance_score`：由 distance 转换得到，越大越相关。

转换公式：

```text
relevance_score = 1 / (1 + distance)
```

因此：

- distance 越接近 0，relevance_score 越接近 1。
- distance 越大，relevance_score 越接近 0。

## 3. 过滤逻辑放在哪里

当前过滤逻辑放在：

```text
app/services/rag_service.py
```

职责边界：

- `app/services/vector_store_service.py`：负责调用 Chroma，并返回 `distance` 和 `relevance_score`。
- `app/services/rag_service.py`：负责 RAG 业务判断，使用 `settings.min_relevance_score` 过滤 chunks。
- `app/tools/rag_tool.py`：不重复实现过滤逻辑，只复用 `RAGService`。

## 4. no-answer 如何触发

触发条件：

1. Chroma 为空：返回“当前知识库还没有可检索内容，请先上传文档后再提问。”
2. Chroma 有返回 chunks，但全部低于 `MIN_RELEVANCE_SCORE`：返回“根据当前知识库资料，无法回答该问题。”
3. 原始检索结果为空：返回“根据当前知识库资料，无法回答该问题。”

触发 no-answer 时：

- 不调用 LLM 生成具体答案。
- `sources` 返回 `[]`。
- `chat_logs` 记录本次 no-answer。
- 日志记录 `NO_RELEVANT_CONTEXT`。

## 5. 如何测试文档内问题

启动服务：

```bash
uvicorn app.main:app --reload
```

上传测试文档：

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -F "file=@data/sample_docs/company_policy.md"
```

提问：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司的退款周期是多久？\",\"top_k\":3}"
```

预期：

- 返回具体 answer。
- `sources` 非空。
- sources 中包含 `distance` 和 `relevance_score`。

## 6. 如何测试文档外问题

提问：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司年会在哪里举办？\",\"top_k\":3}"
```

预期：

- 返回“根据当前知识库资料，无法回答该问题。”
- `sources` 为 `[]`。
- 不调用 LLM 生成具体答案。

Agent RAG 测试：

```bash
curl -X POST "http://127.0.0.1:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司年会在哪里举办？\",\"top_k\":3}"
```

预期：

- `intent=document_qa`
- `tool_used=rag_tool`
- 继承同样的 relevance filtering 和 no-answer 逻辑。

## 7. 当前限制

- `relevance_score = 1 / (1 + distance)` 是简单、可解释的转换方式，不是唯一标准。
- 不同 embedding 模型和 Chroma distance metric 下，distance 分布可能不同，需要人工调参。
- `MIN_RELEVANCE_SCORE=0.2` 是起点，不一定适合所有语料。
- 当前没有 rerank，后续可以引入 reranker 或 metadata filter。
- mock embedding 不能代表真实语义检索质量，真实验收应使用正式 embedding 模型重新入库后测试。
