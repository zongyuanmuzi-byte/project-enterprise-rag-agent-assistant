# Enterprise RAG Agent Assistant 项目结构地图

生成日期：2026-05-28

说明：本文件基于当前仓库静态扫描整理，只记录现状与缺口，不新增业务功能，不修改业务代码。当前代码中多处中文字符串在终端读取时呈现乱码，疑似历史编码问题；本文件仅记录该风险，不直接修复。

## 1. 当前项目文件树

已忽略 `.venv`、`__pycache__`、`.git`、`node_modules`、`.env`、`data/app.db`、`data/chroma_db/` 等本地运行产物或敏感配置。

```text
enterprise-rag-agent-assistant/
|-- .dockerignore
|-- .env.example
|-- .gitignore
|-- Dockerfile
|-- README.md
|-- project_code_snapshot.txt
|-- requirements.txt
|-- 00_project_notes/
|   |-- current_code_summary.md
|   |-- project_structure_map.md
|   |-- stage_01_engineering_foundation.md
|   `-- stage_01_mindmap.md
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- main.py
|   |-- schemas.py
|   |-- api/
|   |   |-- __init__.py
|   |   |-- agent.py
|   |   |-- chat.py
|   |   |-- documents.py
|   |   `-- health.py
|   |-- database/
|   |   |-- __init__.py
|   |   |-- db.py
|   |   `-- models.py
|   |-- prompts/
|   |   |-- __init__.py
|   |   |-- rag_prompt.py
|   |   `-- router_prompt.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- agent_router.py
|   |   |-- chat_service.py
|   |   |-- document_service.py
|   |   |-- embedding_service.py
|   |   |-- graph_agent.py
|   |   |-- langgraph_agent.py
|   |   |-- llm_service.py
|   |   |-- rag_service.py
|   |   |-- tool_executor.py
|   |   `-- vector_store_service.py
|   |-- tools/
|   |   |-- __init__.py
|   |   |-- base.py
|   |   |-- general_chat_tool.py
|   |   |-- mcp_like_schemas.py
|   |   |-- rag_tool.py
|   |   |-- summary_tool.py
|   |   `-- writing_tool.py
|   `-- utils/
|       |-- __init__.py
|       `-- logger.py
|-- data/
|   `-- sample_docs/
|       |-- company_policy.md
|       `-- company_policy.pdf
|-- docs/
|-- scripts/
|   |-- check_chat_logs.py
|   |-- check_chroma_data.py
|   |-- generate_code_summary.py
|   |-- test_agent_chat.py
|   |-- test_embedding_service.py
|   |-- test_graph_agent.py
|   |-- test_index_document_sql.py
|   |-- test_langgraph_agent.py
|   |-- test_pdf_extract.py
|   |-- test_search_indexed_document.py
|   `-- test_vector_store_service.py
`-- tests/
    `-- rag_eval_questions.md
```

## 2. 项目分层说明

1. 用户 / 前端层  
当前缺失。项目目前是 FastAPI 后端服务，没有 Web 前端、CLI 入口或用户上传页面。用户主要通过 Swagger、HTTP API 或脚本调用。

2. API 路由层  
已存在：`app/api/health.py`、`app/api/chat.py`、`app/api/documents.py`、`app/api/agent.py`。分别提供健康检查、RAG 问答、文档索引、Agent 问答与 LangGraph Agent 问答入口。

3. Schema 请求响应层  
已存在：`app/schemas.py`。包含 `ChatRequest`、`ChatResponse`、`DocumentIndexRequest`、`DocumentIndexResponse`、`AgentChatRequest`、`AgentChatResponse`、`SourceItem`、`ErrorResponse`。

4. Service 业务逻辑层  
已存在：`app/services/`。包含文档处理、RAG 主流程、embedding、vector store、LLM、Agent router、tool executor、graph agent、LangGraph agent。`chat_service.py` 仍保留早期 placeholder 聊天服务，但当前 `/chat` 已不再调用它。

5. RAG / Agent 核心层  
已存在：`app/services/rag_service.py`、`app/services/agent_router.py`、`app/services/tool_executor.py`、`app/services/graph_agent.py`、`app/services/langgraph_agent.py`、`app/tools/rag_tool.py`、`app/tools/summary_tool.py`、`app/tools/writing_tool.py`、`app/tools/general_chat_tool.py`、`app/prompts/rag_prompt.py`、`app/prompts/router_prompt.py`。

6. Database + Vector Store 数据层  
已存在：`app/database/db.py`、`app/database/models.py`、`app/services/vector_store_service.py`。SQLite 用于 documents、chunks、chat_logs、feedback；Chroma 用于向量检索。当前没有 Alembic 迁移，也没有独立 repository/DAO 层。

7. LLM / Embedding 外部模型层  
已存在：`app/services/llm_service.py`、`app/services/embedding_service.py`。支持 `mock` 和 `openai_compatible` 两种模式。当前默认 mock，可本地跑通链路，但语义能力有限。

8. 日志 / 测试 / 部署 / 文档支撑层  
已存在：`app/utils/logger.py`、`scripts/`、`tests/rag_eval_questions.md`、`README.md`、`Dockerfile`、`.env.example`、`00_project_notes/`。`docs/` 目录存在但为空；`eval/` 目录当前缺失；自动化 pytest 测试当前缺失。

## 3. 核心文件职责说明

| 文件 | 所属层 | 主要职责 | 接收什么数据 | 输出什么数据 | 被谁调用 | 会调用谁 |
|---|---|---|---|---|---|---|
| `app/main.py` | 应用入口 / API 装配 | 创建 FastAPI app，校验配置，初始化数据库，注册路由和全局异常处理 | 启动时环境配置、HTTP 请求上下文 | FastAPI app、统一错误响应 | Uvicorn、Docker CMD | `validate_settings`、`init_db`、各 API router、`app_logger` |
| `app/config.py` | 配置层 | 定义 Settings，读取 `.env`，校验 chunk、top_k、provider 等配置 | 环境变量、默认配置 | `settings` 对象、配置校验结果 | `main.py`、db、各 service | `pydantic_settings.BaseSettings` |
| `app/schemas.py` | Schema 层 | 定义 API 请求/响应模型与字段校验 | HTTP request body、service 返回 dict | Pydantic model、校验后的字段 | `app/api/*.py` | Pydantic |
| `app/api/health.py` | API 路由层 | 提供 `GET /health` 健康检查 | HTTP GET | `status`、`message` | `main.py` 注册，用户/API 客户端调用 | 无业务 service |
| `app/api/chat.py` | API 路由层 | 提供 `POST /chat` RAG 问答入口 | `ChatRequest`、DB session | `ChatResponse` 或 HTTP error | `main.py` 注册，用户/API 客户端调用 | `get_db`、`RAGService.chat` |
| `app/api/documents.py` | API 路由层 | 提供 `POST /documents/index` 本地文档索引入口 | `DocumentIndexRequest`、DB session | `DocumentIndexResponse` 或 HTTP error | `main.py` 注册，用户/API 客户端调用 | `get_db`、`index_document_for_rag` |
| `app/api/agent.py` | API 路由层 | 提供 `/agent/chat` 与 `/agent/graph-chat`，负责 Agent 请求、日志落库和错误包装 | `AgentChatRequest`、DB session | `AgentChatResponse` | `main.py` 注册，用户/API 客户端调用 | `AgentRouter`、`ToolExecutor`、`LangGraphAgent`、`ChatLog` |
| `app/services/chat_service.py` | Service 层 | 早期 placeholder chat 服务，生成占位回答并写 chat_logs | question、DB session | answer、request_id、latency | 当前未被 API 调用 | `ChatLog`、`app_logger` |
| `app/services/document_service.py` | Service / 文档入库层 | 读取 txt/md/pdf，清洗文本，切 chunk，写 SQLite，生成 embedding，写 Chroma | file_path、DB session | document_id、filename、chunks_count、status | `app/api/documents.py`、scripts | `Document`、`Chunk`、`EmbeddingClient`、`VectorStoreService` |
| `app/services/embedding_service.py` | LLM / Embedding 层 | 统一封装 embedding，支持 mock 与 OpenAI-compatible | 文本列表 | embedding 向量列表 | `document_service.py`、`rag_service.py`、scripts | OpenAI SDK 或本地 mock |
| `app/services/vector_store_service.py` | Vector Store 数据层 | 初始化 Chroma collection，写入 chunks+embeddings，按 query embedding 检索相似 chunk | chunks、embeddings、query_embedding、top_k | added_count 或相似 chunks | `document_service.py`、`rag_service.py`、scripts | `chromadb.PersistentClient` |
| `app/services/rag_service.py` | RAG 核心层 | 串联 query embedding、Chroma retrieval、prompt、LLM、chat_logs | question、top_k、DB session | answer、sources、request_id、latency_ms | `app/api/chat.py`、`app/tools/rag_tool.py` | `EmbeddingClient`、`VectorStoreService`、`LLMClient`、`rag_prompt`、`ChatLog` |
| `app/services/llm_service.py` | LLM 外部模型层 | 统一封装 LLM 生成，支持 mock 与 OpenAI-compatible | prompt | answer 文本 | `rag_service.py`、Agent router、各 tool | OpenAI SDK 或本地 mock |
| `app/services/agent_router.py` | Agent 核心层 | 对用户问题做 intent 分类；LLM 失败时使用规则兜底 | question | intent、reason | `app/api/agent.py`、`graph_agent.py`、`langgraph_agent.py` | `LLMClient`、`router_prompt` |
| `app/services/tool_executor.py` | Agent 核心层 | 根据 intent 选择并执行工具，规范化工具返回 | intent、question、top_k、DB session | tool_used、answer、sources、error | `app/api/agent.py`、graph agents | `RAGTool`、`SummaryTool`、`WritingTool`、`GeneralChatTool` |
| `app/services/graph_agent.py` | Agent 核心层 | 手写 graph-style Agent：router -> tool node -> final node | question、top_k、DB session | AgentState | scripts 或未来 API | `AgentRouter`、`ToolExecutor` |
| `app/services/langgraph_agent.py` | Agent 核心层 | 使用 LangGraph 编排 router、条件边、工具节点、final node | question、top_k、DB session | LangGraphAgentState | `app/api/agent.py`、scripts | `langgraph`、`AgentRouter`、`ToolExecutor` |
| `app/database/db.py` | Database 层 | 创建 SQLAlchemy engine/session/Base，保证 SQLite data 目录存在，初始化表 | `DATABASE_URL` | engine、SessionLocal、get_db、init_db | `main.py`、API、scripts | SQLAlchemy、`app.database.models` |
| `app/database/models.py` | Database 层 | 定义 ORM 表模型：Document、Chunk、ChatLog、Feedback | ORM 字段定义 | 数据表映射 | `init_db`、services、API 日志函数 | SQLAlchemy |
| `app/tools/base.py` | Agent Tool 层 | 定义工具抽象基类 | tool_input | dict result | 各 tool 继承 | `abc.ABC` |
| `app/tools/rag_tool.py` | Agent Tool / RAG 层 | 将 RAGService 封装成 Agent tool | question、top_k、DB session | output、sources、error | `ToolExecutor` | `RAGService.chat` |
| `app/tools/summary_tool.py` | Agent Tool 层 | 总结用户提供内容 | question | output、sources、error | `ToolExecutor` | `LLMClient` |
| `app/tools/writing_tool.py` | Agent Tool 层 | 企业写作、改写、邮件等工具 | question | output、sources、error | `ToolExecutor` | `LLMClient` |
| `app/tools/general_chat_tool.py` | Agent Tool 层 | 普通对话工具 | question | output、sources、error | `ToolExecutor` | `LLMClient` |
| `app/tools/mcp_like_schemas.py` | Agent Tool 支撑层 | 定义类 MCP 的工具 schema，目前主要是 search_documents schema | 无运行输入 | schema dict/list | 当前未被核心流程调用 | 无 |
| `app/prompts/rag_prompt.py` | Prompt 层 | 构造 RAG 系统指令、context、最终 prompt；定义无答案文本 | retrieved chunks、question | context 字符串、prompt 字符串 | `RAGService`、`LLMClient` 引用常量 | `logger` |
| `app/prompts/router_prompt.py` | Prompt 层 | 构造 Agent intent 分类 prompt，定义允许 intent | question | router prompt | `AgentRouter` | 无 |
| `app/utils/logger.py` | 日志层 | 创建统一 logger，按 `LOG_LEVEL` 输出到 stdout | logger name、配置 | Logger 实例 | 全项目 | Python logging |
| `tests/rag_eval_questions.md` | 测试 / 评估层 | 人工 RAG 评测问题集与记录表 | 人工填写测试结果 | expected answers、评测记录 | 项目负责人/测试人员 | 无代码调用 |
| `docs/` | 文档支撑层 | 当前为空 | 当前缺失 | 当前缺失 | 当前缺失 | 当前缺失 |
| `eval/` | 评估支撑层 | 当前缺失 | 当前缺失 | 当前缺失 | 当前缺失 | 当前缺失 |
| `Dockerfile` | 部署层 | 构建 Python 3.11 FastAPI 镜像并启动 uvicorn | requirements、源码 | 可运行容器镜像 | Docker | `uvicorn app.main:app` |
| `README.md` | 文档层 | 项目说明、阶段能力、运行方式初版 | 人工维护 | 项目说明文档 | 开发者、面试展示 | 无代码调用 |

## 4. 当前文档入库数据流

当前已经支持文档入库，但形态是“提交本地文件路径”，不是前端上传文件。支持 `.txt`、`.md`、文本型 `.pdf`；不支持 OCR，不支持删除/更新文档，不支持批量入库 API。

```text
用户提交本地文件路径
↓
POST /documents/index
↓
DocumentIndexRequest 校验 file_path
↓
index_document_for_rag(file_path, db)
↓
read_file() 读取 txt/md/pdf
↓
clean_text() 清洗文本
↓
documents 表创建文档记录
↓
split_text() 切 chunk
↓
chunks 表写入 chunk 内容
↓
EmbeddingClient.embed_texts() 生成 chunk embeddings
↓
VectorStoreService.add_chunks() 写入 Chroma
↓
SQLite commit
↓
返回 document_id、filename、chunks_count、status=indexed
```

当前缺失或不完整点：
- 没有真正的“文件上传”接口，只能传服务器本地路径。
- 没有文档去重、重复索引保护；Chroma 使用 `doc_{document_id}_chunk_{chunk_index}`，同一数据库 id 不重复时可用，但重新索引同文件会产生新 document。
- SQLite 与 Chroma 没有强事务一致性；如果 Chroma 写入成功但 SQL commit 失败，可能出现不一致。
- 没有文档更新、删除、重建索引接口。
- PDF 只支持可复制文本，不支持扫描件 OCR。
- `DocumentIndexResponse.status` 示例仍有旧值 `indexed_to_sql`，实际 `index_document_for_rag` 返回 `indexed`。

## 5. 当前用户提问数据流

当前已经支持用户提问。`POST /chat` 是直接 RAG 问答，不走 `chat_service.py`；`chat_service.py` 属于早期 placeholder 遗留服务。

```text
用户提问
↓
POST /chat
↓
ChatRequest 校验 question/top_k
↓
RAGService.chat()
↓
EmbeddingClient.embed_texts() 生成 question embedding
↓
VectorStoreService.search_similar_chunks() 从 Chroma 检索 top-k chunks
↓
build_context_from_chunks()
↓
build_rag_prompt()
↓
LLMClient.generate_answer()
↓
返回 answer + sources + request_id + latency_ms
↓
chat_logs 写入 question、answer、retrieved_chunks、latency、error
```

当前缺失或不完整点：
- 没有独立 `retrieval_service.py`；检索逻辑直接在 `RAGService` 调用 `VectorStoreService`。
- `settings.min_relevance_score` 已配置但当前检索流程未使用，没有按相似度阈值过滤 sources。
- 默认 mock embedding/LLM 只能验证工程链路，不代表真实语义效果。
- 如果 Chroma 为空，`VectorStoreService.search_similar_chunks()` 抛 ValueError，最终 `/chat` 返回 500，而不是更友好的“请先入库文档”业务错误。
- `chat_logs` 已写入，但没有查询聊天历史的 API。

## 6. Agent 化后的目标调用流

用户要求的目标调用流如下，并标注当前状态：

```text
用户问题
↓
app/api/chat.py
↓
chat_service.py
↓
agent_service.py
↓
router.py 判断 intent
↓
executor.py 调用 tool
↓
rag_tool.py 调用 rag_service.py
↓
返回工具结果
↓
生成最终回答
```

当前实际情况：

| 目标节点 | 当前对应文件 | 状态 | 说明 |
|---|---|---|---|
| 用户问题 | HTTP API | 已存在 | 通过 `/chat`、`/agent/chat`、`/agent/graph-chat` 接收 |
| `app/api/chat.py` | `app/api/chat.py` | 已存在，但不走 Agent | 当前直接调用 `RAGService` |
| `chat_service.py` | `app/services/chat_service.py` | 已存在，但当前未被 `/chat` 调用 | 仍是早期 placeholder 逻辑 |
| `agent_service.py` | 当前缺失 | 缺失 | 没有统一 AgentService；Agent 编排逻辑分散在 `api/agent.py`、`graph_agent.py`、`langgraph_agent.py` |
| `router.py` 判断 intent | `app/services/agent_router.py` | 已存在，但命名不同 | 当前叫 `AgentRouter` |
| `executor.py` 调用 tool | `app/services/tool_executor.py` | 已存在，但命名不同 | 当前叫 `ToolExecutor` |
| `rag_tool.py` 调用 rag_service.py | `app/tools/rag_tool.py` | 已存在 | 已封装 `RAGService.chat` |
| 返回工具结果 | `ToolExecutor.execute()` | 已存在 | 统一返回 `tool_used`、`answer`、`sources`、`error` |
| 生成最终回答 | `api/agent.py` / graph final_node | 部分存在 | 当前主要是工具直接生成 answer；final node 只做轻量规范化，没有二次综合回答 |

当前已有两个 Agent 路径：

```text
POST /agent/chat
↓
AgentRouter.route()
↓
ToolExecutor.execute()
↓
RAGTool / SummaryTool / WritingTool / GeneralChatTool
↓
保存 ChatLog
↓
AgentChatResponse
```

```text
POST /agent/graph-chat
↓
LangGraphAgent.run()
↓
router node
↓
conditional edge
↓
rag / summary / writing / chat node
↓
final node
↓
保存 ChatLog
↓
AgentChatResponse
```

## 7. 当前缺失模块清单

高优先级：
- 自动化测试文件：例如 `tests/test_health.py`、`tests/test_documents.py`、`tests/test_chat.py`。当前只有人工评测 Markdown，没有 pytest。
- `retrieval_service.py` 或等价检索服务抽象：当前检索逻辑嵌在 `rag_service.py` 中，短期可用，但后续过滤、重排、阈值会膨胀。
- 文档上传 API：当前只有本地路径索引，不是真正用户上传。
- 文档更新/删除/重建索引能力：避免 SQLite 与 Chroma 长期不一致。
- 友好的空向量库错误处理：当前 Chroma 为空时 `/chat` 容易变成 500。
- 编码修复/文档重写：README、sample docs、prompts、测试问题中大量中文显示异常，影响理解、展示和 mock 逻辑可靠性。

中优先级：
- `agent_service.py`：统一封装 Agent 调用，减少 `api/agent.py` 承担编排细节。
- `app/agent/` 包：当前 Agent 核心在 `app/services/` 与 `app/tools/`，如果继续扩展，可将 router/executor/state/graph 迁移到更清晰的 Agent 包；但现在不建议为了目录好看而重构。
- `feedback.py` API/service：数据库已有 `Feedback` 表，但没有反馈写入接口。
- `eval/run_eval.py`：当前只有人工问题集，没有自动评估脚本。
- relevance score 过滤或 rerank：`min_relevance_score` 已配置但未使用。
- 数据库迁移：当前 `create_all` 适合早期，后续需要 Alembic。

低优先级：
- `docker-compose.yml`：当前只有 Dockerfile，单服务演示够用；多服务部署时再补。
- `docs/` 下部署文档、API 文档、架构图：目录存在但为空。
- 面试展示文档：可以后续整理 README、架构图、关键链路说明。
- CI 配置：如 GitHub Actions，在自动化测试成型后再补。
- 前端页面：当前项目定位更像后端 RAG/Agent 工程，前端不是阶段 1 必需。

## 8. 下一步开发优先级建议

阶段 1 下一步建议先补“工程可验证性”和“基础链路稳定性”，不要急着扩业务功能。

1. `/health` 是否可用：已存在 `GET /health`，建议补一个最小自动化测试，确认应用能启动并返回 `status=ok`。
2. `main.py` 是否清晰：整体清晰，已集中注册 router、异常处理、启动初始化；注意 `create_app()` 导入时会初始化 DB 和 service，测试时可能产生副作用。
3. `config.py` 是否可用：已可用，配置覆盖 RAG、Chroma、Embedding、LLM；建议后续补 `.env.example` 与 README 的同步说明。
4. `database/db.py` 是否可用：已可用，适合本地开发；生产化前需要 Alembic 与更明确的数据库生命周期管理。
5. `models.py` 是否合理：当前四张表覆盖文档、chunk、聊天日志、反馈；Feedback 有模型但无 API。
6. `schemas.py` 是否清晰：基础可用，但文件开始变大；后续可以按 chat/documents/agent 拆分，但现在不必重构。
7. logger 是否存在：已存在 `app/utils/logger.py`，全局可用；后续可加入 request_id 中间件。
8. README 是否有初版：已存在，但当前中文显示乱码，应优先修复展示文档和样例文档编码，否则影响面试展示和项目理解。

建议阶段 1 最优先补：
- 最小 pytest：health、config validation、db init、document split。
- 修复或重写 README、sample docs、prompts/test questions 的中文编码内容。
- 让空知识库问答返回业务可理解错误或固定提示。
- 增加一条“文档入库后再提问”的端到端脚本或测试说明。

## 9. 我必须深入理解的部分

- FastAPI 请求如何从 `main.py` 注册到 `app/api/*.py`。
- Pydantic schema 如何做请求校验、响应约束和 Swagger 文档生成。
- `get_db()` 如何给每个请求提供 SQLAlchemy session，以及 commit/rollback 的位置。
- 文档入库链路：读取文件、清洗、chunk、写 SQLite、embedding、写 Chroma。
- RAG 问答链路：question embedding、vector retrieval、context、prompt、LLM、sources、chat_logs。
- SQLite 与 Chroma 的职责边界：SQLite 存结构化业务记录，Chroma 存向量检索数据。
- mock provider 与真实 OpenAI-compatible provider 的差异：mock 只用于验证工程链路。
- Agent 的三层关系：`AgentRouter` 判断 intent，`ToolExecutor` 选择 tool，tool 调用具体 service。
- 日志与错误处理：哪里抛异常、哪里转换成 HTTP error、哪里落 chat_logs。
- 当前代码中的编码风险：乱码会影响 prompt、mock LLM 关键字匹配、README 展示质量。

## 10. 我只需要大概理解的部分

- Chroma 内部索引算法和底层向量存储实现，当前只需知道如何 add/query/count。
- OpenAI SDK 的底层 HTTP 细节，当前只需理解 embeddings 和 chat completions 的输入输出。
- LangGraph 的高级特性，如 checkpoint、human-in-the-loop、多轮复杂状态，目前只用了最小 StateGraph。
- Docker 镜像分层优化和生产级部署细节，当前 Dockerfile 足够演示。
- SQLAlchemy relationship 的高级加载策略，目前只需理解 Document、Chunk、ChatLog、Feedback 表关系。
- PDF 解析底层细节，当前只需知道 `pypdf` 不支持 OCR。
- MCP-like schema 的完整协议细节，当前 `mcp_like_schemas.py` 只是工具 schema 草稿。

## 11. 可以交给 AI coding 工具实现的部分

可以让 Codex / Claude Code / Cursor 实现，但你需要负责验收：

- 补最小 pytest 测试：`/health`、schema 校验、`clean_text`、`split_text`、mock embedding、mock vector store。
- 修复或重写 README、docs、测试问题集中的中文乱码内容。
- 给空知识库场景补更友好的错误响应和测试。
- 新增 `eval/run_eval.py`，读取 `tests/rag_eval_questions.md` 或结构化评测文件并批量调用 API。
- 新增文档上传接口，但需要你确认安全边界、文件大小、允许类型、存储位置。
- 新增 feedback API/service，写入现有 `Feedback` 表。
- 整理 `docs/architecture.md`、`docs/api_examples.md`、`docs/demo_script.md`。
- 补 `docker-compose.yml` 和部署说明。
- 在不改变业务语义的前提下，把 Agent 编排收敛到 `agent_service.py`，但这属于后续小重构，当前阶段不建议马上做。

验收时你需要重点看：
- API 路径、请求/响应字段是否符合你的项目叙事。
- 文档入库和问答是否能端到端跑通。
- sources 是否真的来自检索结果，而不是模型编造。
- 失败场景是否有可解释的错误信息。
- 新增测试是否稳定，不依赖真实外部模型 key。
