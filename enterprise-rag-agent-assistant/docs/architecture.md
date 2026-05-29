# 系统架构说明

本文档说明 Enterprise RAG Agent Assistant 的当前主线架构。

## 1. 项目分层架构

```text
Client
  ↓
API Layer
  ↓
Schema Layer
  ↓
Service Layer
  ↓
Agent / Tool / RAG Core
  ↓
Database + Vector Store
  ↓
LLM / Embedding Provider
```

项目采用分层结构，核心目标是让 API 层保持轻量，让业务编排进入 Service 层，让 Agent 调度和 Tool 调用独立于普通 RAG 问答链路。

## 2. API 层

目录：

```text
app/api/
```

职责：

- 接收 HTTP 请求
- 注入数据库 session
- 调用 service
- 返回 Pydantic response
- 将业务异常转换为 HTTP 响应

主线 API：

- `GET /health`
- `POST /documents/upload`
- `POST /chat`
- `POST /agent/chat`
- `POST /feedback`

## 3. Schema 层

文件：

```text
app/schemas.py
```

职责：

- 定义请求结构
- 定义响应结构
- 做基础字段校验

核心 schema：

- `ChatRequest`
- `ChatResponse`
- `DocumentIndexRequest`
- `DocumentIndexResponse`
- `AgentChatRequest`
- `AgentChatResponse`
- `SourceItem`

## 4. Service 层

目录：

```text
app/services/
```

职责：

- 承载主要业务流程
- 串联数据库、向量库、模型服务
- 避免 API 层直接写复杂业务逻辑

核心服务：

- `document_service.py`：文档读取、清洗、chunk、入库、向量写入
- `rag_service.py`：RAG 问答主流程
- `agent_service.py`：Agent 主线编排
- `llm_service.py`：LLM 客户端
- `embedding_service.py`：Embedding 客户端
- `vector_store_service.py`：Chroma 封装
- `feedback_service.py`：写入用户反馈

## 5. Agent 层

目录：

```text
app/agent/
```

职责：

- 判断用户 intent
- 根据 intent 调用对应 tool

核心文件：

- `router.py`：`AgentRouter`
- `executor.py`：`ToolExecutor`

允许 intent：

- `document_qa`
- `summary`
- `writing`
- `general_chat`

## 6. Tool 层

目录：

```text
app/tools/
```

职责：

- 将具体能力封装成 Agent 可调用工具
- 每个 tool 输入输出格式尽量统一

当前工具：

- `rag_tool.py`：调用 `RAGService`
- `summary_tool.py`：总结任务
- `writing_tool.py`：写作任务
- `general_chat_tool.py`：普通解释和闲聊

说明：

- `rag_tool` 返回 sources。
- 非 RAG 工具不返回 sources。

## 7. Database 层

目录：

```text
app/database/
```

职责：

- 管理 SQLAlchemy engine 和 session
- 定义 ORM models

当前 SQLite 表：

- `documents`：文档元数据
- `chunks`：文档切分片段
- `chat_logs`：问答日志
- `feedback`：后续反馈扩展

Feedback 与 chat_logs 的关系：

```text
chat_logs.id -> feedback.chat_log_id
```

## 8. Vector Store 层

文件：

```text
app/services/vector_store_service.py
```

职责：

- 初始化 Chroma
- 创建或获取 collection
- 写入 chunk embeddings
- 根据 query embedding 检索相似 chunks

当前向量数据保存在：

```text
data/chroma_db
```

## 9. LLM / Embedding 层

文件：

```text
app/services/llm_service.py
app/services/embedding_service.py
```

职责：

- 封装模型调用
- 支持 mock 与 OpenAI-compatible provider
- 避免 API key 泄露到日志

当前真实模型：

- LLM：DeepSeek
- Embedding：智谱 `embedding-3`

## 10. RAG 数据流

```text
用户提问
↓
POST /chat
↓
ChatRequest
↓
RAGService.chat()
↓
EmbeddingClient 生成 query embedding
↓
VectorStoreService 从 Chroma 检索 chunks
↓
build_context_from_chunks()
↓
build_rag_prompt()
↓
LLMClient 调用 DeepSeek
↓
返回 answer + sources
↓
写入 chat_logs
```

## 11. Agent 数据流

```text
用户请求
↓
POST /agent/chat
↓
AgentService.chat()
↓
AgentRouter.route()
↓
ToolExecutor.execute()
↓
根据 intent 调用 tool
↓
rag_tool / summary_tool / writing_tool / general_chat_tool
↓
返回 answer + sources
↓
写入 chat_logs
```

Agent 主线和 RAG 主线保持解耦：`/chat` 直接走 RAG，`/agent/chat` 先路由再调用 tool。

## 12. Feedback 数据流

```text
用户对回答进行评分
↓
POST /feedback
↓
FeedbackRequest 校验 chat_log_id / rating
↓
FeedbackService 检查 chat_log 是否存在
↓
写入 feedback 表
↓
返回 feedback_id、chat_log_id、rating、comment、status
```
