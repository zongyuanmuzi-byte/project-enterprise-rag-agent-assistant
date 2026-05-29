# Enterprise RAG Agent Assistant 第一阶段重构记录

生成日期：2026-05-28

## 1. 本次重构目标

本次重构目标是把当前项目从实验性混合结构，收敛成更清晰的作品级后端项目主线。核心主线只围绕：

- 文件上传
- 文档入库
- RAG 问答
- Agent 调度
- answer + sources
- chat_logs
- feedback / eval 后续扩展

本阶段不引入前端、不引入 Redis/Celery/PostgreSQL、不重写 RAGService、不大改数据库表结构、不删除核心业务文件、不做复杂 LangGraph 重构。

## 2. 新增了哪些文件

- `app/agent/__init__.py`
- `app/agent/router.py`
- `app/agent/executor.py`
- `app/services/agent_service.py`
- `00_project_notes/refactor_plan.md`

其中：

- `app/agent/router.py` 成为主线 Agent intent 路由模块。
- `app/agent/executor.py` 成为主线 tool 执行模块。
- `app/services/agent_service.py` 统一编排 Agent 主流程。

## 3. 移动或弱化了哪些文件

没有删除核心业务文件，没有物理移动 `graph_agent.py` 或 `langgraph_agent.py`。

已弱化为 experimental：

- `app/services/graph_agent.py`
- `app/services/langgraph_agent.py`
- `POST /agent/graph-chat`

主线 Agent API 现在是：

```text
POST /agent/chat
```

兼容旧 import：

- `app/services/agent_router.py` 保留，但只 re-export `app.agent.router.AgentRouter`
- `app/services/tool_executor.py` 保留，但只 re-export `app.agent.executor.ToolExecutor`

这样旧脚本或旧 import 不会立即断，同时避免两套重复逻辑继续分叉。

## 4. 新的主线数据流

```text
用户请求
↓
FastAPI API 层
↓
Pydantic schema 校验
↓
Service 层统一编排
↓
RAG / Agent / Tool 核心逻辑
↓
Database + Vector Store
↓
返回结构化响应
```

API 层只保留薄入口，尽量不直接写复杂业务编排。

## 5. 文件上传数据流

新增主线入口：

```text
POST /documents/upload
↓
UploadFile 接收文件
↓
校验扩展名 .txt / .md / .pdf
↓
保存到 data/uploads/
↓
调用 index_document_for_rag(file_path, db)
↓
read_file()
↓
clean_text()
↓
split_text()
↓
写入 documents / chunks
↓
EmbeddingClient 生成 embeddings
↓
VectorStoreService 写入 Chroma
↓
返回 document_id、filename、chunks_count、status
```

保留开发入口：

```text
POST /documents/index
```

该入口仍然通过本地 `file_path` 入库，便于本地脚本和调试使用。

## 6. RAG 数据流

RAG 主流程保持不破坏：

```text
POST /chat
↓
ChatRequest
↓
RAGService.chat()
↓
EmbeddingClient 生成 question embedding
↓
VectorStoreService 从 Chroma 检索 top-k chunks
↓
build_context_from_chunks()
↓
build_rag_prompt()
↓
LLMClient.generate_answer()
↓
返回 answer + sources + request_id + latency_ms
↓
写入 chat_logs
```

`RAGService` 没有被重写，本阶段只保证它继续作为问答主链路可用。

## 7. Agent 数据流

新的主线 Agent 数据流：

```text
POST /agent/chat
↓
AgentChatRequest
↓
AgentService.chat()
↓
AgentRouter.route()
↓
ToolExecutor.execute()
↓
RAGTool / SummaryTool / WritingTool / GeneralChatTool
↓
返回 answer + sources + tool_used + intent
↓
写入 chat_logs
↓
AgentChatResponse
```

其中：

- `AgentRouter` 位于 `app/agent/router.py`
- `ToolExecutor` 位于 `app/agent/executor.py`
- `AgentService` 位于 `app/services/agent_service.py`
- `RAGTool` 继续调用 `RAGService`

实验性 Agent 数据流：

```text
POST /agent/graph-chat
↓
LangGraphAgent
↓
experimental graph flow
```

该路径保留给本地实验，不作为作品主线。

## 8. 后续还需要优化什么

高优先级：

- 给 `/health`、`/documents/index`、`/documents/upload`、`/chat`、`/agent/chat` 补最小自动化测试。
- 修复 README、prompt、sample docs、测试问题中的中文乱码问题。
- 给空向量库场景返回更友好的业务提示，避免普通用户看到 500。
- 为上传文件增加大小限制和更稳妥的文件名/重复文件策略。

中优先级：

- 将 feedback 表补成 API + service。
- 增加简单 eval 脚本，但不在本阶段实现。
- 后续考虑把 schema 拆成 `schemas/chat.py`、`schemas/documents.py`、`schemas/agent.py`，但当前不急。
- 后续考虑为 SQLite/Chroma 一致性增加补偿或重建索引脚本。

低优先级：

- 整理 `docs/` 下的架构说明、API 示例和面试展示文档。
- Docker Compose、CI、部署文档等放到作品稳定后再做。
