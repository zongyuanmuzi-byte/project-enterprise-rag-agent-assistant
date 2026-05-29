# API 示例

本文档记录 Enterprise RAG Agent Assistant 当前主线 API。

## 1. GET /health

作用：检查服务是否启动。

请求方式：

```http
GET /health
```

示例请求：

```bash
curl http://127.0.0.1:8000/health
```

示例响应：

```json
{
  "status": "ok",
  "message": "Enterprise RAG Agent Assistant is running"
}
```

适用场景：

- 本地启动后确认服务可用
- 简单健康检查

## 2. POST /documents/upload

作用：上传 `.txt`、`.md`、`.pdf` 文档，完成文档入库和向量索引。

请求方式：

```http
POST /documents/upload
Content-Type: multipart/form-data
```

示例请求：

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -F "file=@data/sample_docs/company_policy.md"
```

示例响应：

```json
{
  "document_id": 1,
  "filename": "company_policy.md",
  "chunks_count": 3,
  "status": "indexed"
}
```

适用场景：

- 上传公司制度文档
- 上传政策、合同、FAQ
- 构建企业知识库

## 3. POST /chat

作用：基础 RAG 问答，根据知识库内容回答用户问题。

请求方式：

```http
POST /chat
Content-Type: application/json
```

示例请求：

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司的退款周期是多久？\",\"top_k\":3}"
```

示例响应：

```json
{
  "answer": "根据知识库资料，退款通常会在审核通过后由财务部门处理，具体周期请以文档条款为准。",
  "sources": [
    {
      "filename": "company_policy.md",
      "chunk_index": 0,
      "document_id": 1,
      "content": "客户提交退款申请后，客服团队会先完成审核，财务部门会在审核通过后处理退款。",
      "distance": 0.23
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "latency_ms": 320
}
```

适用场景：

- 直接进行企业知识库问答
- 验证 RAG 检索和 sources 是否正确
- 展示文档外问题拒答

## 4. POST /agent/chat

作用：Agent 统一入口。系统先判断用户 intent，再调用对应工具。

请求方式：

```http
POST /agent/chat
Content-Type: application/json
```

示例请求 1：知识库问答

```bash
curl -X POST "http://127.0.0.1:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"公司的退款周期是多久？\",\"top_k\":3}"
```

示例响应 1：

```json
{
  "intent": "document_qa",
  "tool_used": "rag_tool",
  "answer": "根据知识库资料，退款通常会在审核通过后由财务部门处理。",
  "sources": [
    {
      "filename": "company_policy.md",
      "chunk_index": 0,
      "document_id": 1,
      "content": "客户提交退款申请后，客服团队会先完成审核，财务部门会在审核通过后处理退款。",
      "distance": 0.23
    }
  ],
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "latency_ms": 420,
  "error": null
}
```

示例请求 2：写作任务

```bash
curl -X POST "http://127.0.0.1:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"帮我写一封英文邮件，告诉客户我们已经收到退款申请。\"}"
```

示例响应 2：

```json
{
  "intent": "writing",
  "tool_used": "writing_tool",
  "answer": "Subject: Refund Request Received\n\nDear Customer,\n\nWe have received your refund request...",
  "sources": [],
  "request_id": "550e8400-e29b-41d4-a716-446655440002",
  "latency_ms": 380,
  "error": null
}
```

适用场景：

- 用一个接口承载多类 AI 任务
- 展示 Agent Router 与 ToolExecutor
- 同时支持 RAG、总结、写作、普通解释

## 5. POST /feedback

作用：对某次问答记录提交评分和备注。

请求方式：

```http
POST /feedback
Content-Type: application/json
```

示例请求：

```bash
curl -X POST "http://127.0.0.1:8000/feedback" \
  -H "Content-Type: application/json" \
  -d "{\"chat_log_id\":1,\"rating\":1,\"comment\":\"答案没有引用正确政策\"}"
```

示例响应：

```json
{
  "feedback_id": 1,
  "chat_log_id": 1,
  "rating": 1,
  "comment": "答案没有引用正确政策",
  "status": "created"
}
```

适用场景：

- 记录用户对回答质量的评分
- 标记错误引用、检索失败或回答不完整
- 后续补充 eval case 和优化 RAG 检索
