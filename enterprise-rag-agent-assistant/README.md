# Enterprise RAG Agent Assistant

Enterprise RAG Agent Assistant 是一个面向企业知识库场景的 RAG + Agent 后端项目。它以 FastAPI 为服务入口，支持上传企业文档、构建向量知识库、基于文档进行问答，并通过 Agent Router 将用户请求分发给不同工具。

这是一个 production-minded learning project / portfolio project，目标是展示一个 AI 应用后端从工程结构、模型接入、RAG 数据流到 Agent 调度的完整闭环。项目不宣称 production-ready，但设计时尽量贴近真实工程实践。

## 1. 项目简介

本项目实现了一个企业知识库问答助手：

- 用户上传公司政策、制度、合同、FAQ 等文档。
- 系统解析文档并切分为 chunks。
- 使用智谱 `embedding-3` 生成 chunk embeddings。
- 使用 Chroma 保存向量索引。
- 用户提问时，系统检索相关 chunks，构造 RAG prompt。
- 使用 DeepSeek 作为 LLM 生成回答。
- 返回 `answer + sources`。
- Agent 模式下，系统先判断 intent，再调用对应 tool。

## 2. 项目目标

项目目标不是做一个大而全的平台，而是完成一个清晰、可讲解、可运行的 AI 应用后端作品：

- 建立标准 FastAPI 后端分层。
- 跑通企业文档入库链路。
- 跑通真实 LLM + Embedding 接入链路。
- 跑通基础 RAG 问答。
- 支持文档外问题拒答。
- 支持 Agent Router + ToolExecutor 调度。
- 保留 feedback / eval 的后续扩展空间。

## 3. 核心功能

- `GET /health`：服务健康检查。
- `POST /documents/upload`：上传 `.txt`、`.md`、`.pdf` 文档并入库。
- `POST /chat`：基础 RAG 问答。
- `POST /agent/chat`：Agent 调度入口。
- `POST /feedback`：对某次 chat_logs 记录提交评分和反馈。
- 文档解析、文本清洗、chunk 切分。
- SQLite 保存 `documents`、`chunks`、`chat_logs`。
- Chroma 保存 chunk embeddings。
- DeepSeek LLM 生成回答。
- 智谱 `embedding-3` 生成向量。
- `answer + sources` 返回。
- 文档外问题拒答。
- Agent 工具：`rag_tool`、`summary_tool`、`writing_tool`、`general_chat_tool`。

## 4. 技术栈

- Web 框架：FastAPI
- 数据校验：Pydantic
- ORM：SQLAlchemy
- 关系型数据库：SQLite
- 向量数据库：Chroma
- LLM：DeepSeek
- Embedding：智谱 `embedding-3`
- 模型接口：OpenAI-compatible API
- 日志：Python logging
- 测试骨架：pytest + FastAPI TestClient

## 5. 系统架构

```text
User / API Client
        |
        v
FastAPI API Layer
        |
        v
Pydantic Schemas
        |
        v
Service Layer
        |
        +--> Document Service -> SQLite + Chroma
        |
        +--> RAG Service -> Embedding -> Vector Search -> Prompt -> LLM
        |
        +--> Agent Service -> AgentRouter -> ToolExecutor -> Tools
```

主要目录：

```text
app/
  api/          API 路由层
  agent/        Agent Router / Executor 主线
  services/     RAG、文档、模型、Agent 编排服务
  tools/        Agent tools
  database/     SQLAlchemy DB 连接与 ORM models
  prompts/      RAG / Router prompt
  utils/        日志工具
```

## 6. 文件上传与文档入库流程

```text
用户上传文档
↓
POST /documents/upload
↓
保存到 data/uploads/
↓
读取 txt / md / pdf
↓
文本清洗
↓
chunk 切分
↓
documents / chunks 写入 SQLite
↓
调用智谱 embedding-3 生成 embeddings
↓
写入 Chroma
↓
返回 document_id、filename、chunks_count、status
```

## 7. RAG 问答流程

```text
用户提问
↓
POST /chat
↓
ChatRequest 校验
↓
问题生成 embedding
↓
Chroma 检索 top-k chunks
↓
构造 context
↓
构造 RAG prompt
↓
DeepSeek 生成回答
↓
返回 answer + sources
↓
写入 chat_logs
```

如果知识库为空，系统会返回友好提示。  
如果问题超出文档范围，系统会拒答或提示资料不足。

## 8. Agent 调度流程

```text
用户请求
↓
POST /agent/chat
↓
AgentService
↓
AgentRouter 判断 intent
↓
ToolExecutor 调用 tool
↓
rag_tool / summary_tool / writing_tool / general_chat_tool
↓
返回统一 AgentChatResponse
↓
写入 chat_logs
```

允许的 intent：

- `document_qa`
- `summary`
- `writing`
- `general_chat`

说明：

- RAG 工具会返回 sources。
- 非 RAG 工具不返回 sources。
- `/agent/graph-chat` 是实验接口，已从 Swagger 主线隐藏。

## 9. API 列表

主线接口只有：

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/documents/upload` | 上传文档并入库 |
| POST | `/chat` | 基础 RAG 问答 |
| POST | `/agent/chat` | Agent 调度问答 |
| POST | `/feedback` | 用户反馈记录 |

隐藏或开发接口：

- `POST /documents/index`
- `POST /agent/graph-chat`

## 10. 环境变量配置

使用 `.env` 配置本地模型和数据库连接。  
`.env` 包含真实 API key，不要提交 GitHub。

示例：

```env
LOG_LEVEL=INFO

DATABASE_URL=sqlite:///./data/app.db

CHUNK_SIZE=800
CHUNK_OVERLAP=120
TOP_K=3
MIN_RELEVANCE_SCORE=0.2

CHROMA_PATH=data/chroma_db
CHROMA_COLLECTION_NAME=enterprise_knowledge_base

LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://your-deepseek-compatible-endpoint/v1
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=your_deepseek_model

EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://your-zhipu-compatible-endpoint/v1
EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_MODEL=embedding-3
```

本地测试可以使用：

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
```

重要：切换 embedding provider 或 embedding model 后，必须清空：

```text
data/chroma_db
data/app.db
```

然后重新上传文档。原因是不同 embedding 模型生成的向量不在同一向量空间，旧索引无法与新 query embedding 正确比较。

## 11. 本地运行方式

### Docker Compose 一键启动

本地 demo 推荐使用 Docker Compose 同时启动后端和前端：

```bash
docker compose up --build
```

访问地址：

```text
Frontend: http://localhost:5173
Backend Health: http://localhost:8010/health
Backend Docs: http://localhost:8010/docs
```

关闭服务：

```bash
docker compose down
```

如果需要清空知识库数据：

```bash
rm -rf data/chroma_db
rm -f data/app.db
```

说明：后端容器内部仍监听 `8000`，通过 Compose 映射到宿主机 `8010`；前端浏览器请求后端时使用 `http://localhost:8010`。

### Tencent Cloud Production Simulation

本地默认仍使用 SQLite + local uploads + Chroma：

```env
DATABASE_URL=sqlite:///./data/app.db
STORAGE_PROVIDER=local
VECTOR_STORE_PROVIDER=chroma
```

腾讯云生产流程模拟模式预留了 COS + MySQL + VectorDB 配置：

```env
STORAGE_PROVIDER=cos
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname?charset=utf8mb4
VECTOR_STORE_PROVIDER=tencent_vectordb
```

详细部署准备和验收流程见 [docs/tencent_cloud_deployment.md](docs/tencent_cloud_deployment.md)。

### 后端本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --reload
```

访问 Swagger：

```text
http://127.0.0.1:8000/docs
```

## 12. 测试方式

运行 pytest：

```bash
pytest -q
```

当前测试是最小骨架，主要用于确认：

- `/health` 可访问
- AgentRouter intent 分类稳定
- `/documents/upload` 接口存在并可接受 markdown 文件
- `/chat` 返回结构包含 `answer`、`sources`、`request_id`、`latency_ms`

手动 eval：

```bash
python eval/run_eval.py
```

`eval/run_eval.py` 默认调用本地 `http://127.0.0.1:8000/agent/chat`，读取 `eval/eval_dataset.json`，检查 tool 路由、关键词、sources 和 no-answer 行为。

## 13. 当前验证结果

已人工验收：

- `/documents/upload` 文件上传成功
- 文档解析、清洗、chunk 切分成功
- SQLite 写入 `documents`、`chunks`、`chat_logs`
- Chroma 写入 chunk embeddings
- DeepSeek LLM 接入成功
- 智谱 `embedding-3` 接入成功
- `/chat` RAG 问答成功
- `answer + sources` 返回成功
- 文档外问题拒答成功
- `/agent/chat` Agent 调度成功
- `/feedback` 可以写入用户评分和备注
- `rag_tool`、`summary_tool`、`writing_tool`、`general_chat_tool` 均已通过人工验收

## 14. 项目亮点

- 完整 AI 应用后端闭环：上传、入库、检索、生成、返回 sources。
- 清晰分层：API、Schema、Service、Agent、Tool、Database、Vector Store、Model Client。
- 支持真实模型：DeepSeek + 智谱 `embedding-3`。
- 支持 mock 模式：方便本地开发和测试，不依赖真实 API key。
- RAG 与 Agent 分离：基础 `/chat` 保持简单，`/agent/chat` 负责 intent 和 tool 调度。
- 可解释返回：RAG 问答返回 sources，便于验证答案来源。
- 为后续 feedback / eval 留出结构空间。
- 已补充 feedback API 和轻量 eval 脚本，形成最小质量闭环。

## 15. 当前限制

- 不是 production-ready 项目。
- 当前仍使用 SQLite，适合学习、演示和小规模本地运行。
- 上传文件大小、重复文档、删除文档、重建索引尚未完整产品化。
- PDF 解析不支持 OCR。
- 自动化测试仍是最小骨架。
- feedback 目前只支持创建，不支持查询、更新、删除。
- eval 目前是轻量手动脚本，不是完整评测平台。
- 检索质量还有继续优化空间，例如 relevance threshold、rerank、metadata filter。

## 16. 后续优化计划

- 扩展 feedback 查询和统计。
- 增强 eval 数据集和评分逻辑。
- 优化检索质量：相似度阈值、rerank、chunk 策略。
- 增加文档删除、重新索引、重复文件处理。
- 整理面试展示材料和架构图。
- 在项目稳定后再考虑 CI 和更完整的部署方案。

## 17. 简历表达

中文示例：

> Enterprise RAG Agent Assistant：基于 FastAPI 构建企业知识库 RAG + Agent 后端系统，支持文档上传、解析、chunk 切分、SQLite 元数据存储、Chroma 向量检索、DeepSeek LLM 生成回答、智谱 embedding-3 向量化，并实现 AgentRouter + ToolExecutor 调度 rag、summary、writing、general chat 等工具，返回 answer + sources，具备 chat_logs 记录和后续 feedback/eval 扩展空间。

英文示例：

> Built a production-minded portfolio backend for an Enterprise RAG Agent Assistant using FastAPI, SQLite, Chroma, DeepSeek LLM, and Zhipu embedding-3. Implemented document upload and indexing, RAG question answering with answer + sources, and an AgentRouter/ToolExecutor flow for routing document QA, summarization, writing, and general chat tasks.
