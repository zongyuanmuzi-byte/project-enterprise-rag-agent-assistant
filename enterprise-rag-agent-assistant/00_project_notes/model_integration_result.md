# Enterprise RAG Agent Assistant 模型接入结果记录

生成日期：2026-05-28

## 1. 本阶段目标

本阶段目标是把项目从 mock 链路推进到真实模型可用状态，并把当前成果固化成可复盘、可展示、可继续迭代的工程记录。

本阶段重点不是新增业务功能，而是确认以下主线能力已经跑通：

- `/documents/upload` 文件上传与文档入库
- 智谱 `embedding-3` 向量化接入
- DeepSeek LLM 接入
- `/chat` RAG 问答
- 文档外问题拒答
- `/agent/chat` Agent 调度
- `rag_tool`、`summary_tool`、`writing_tool`、`general_chat_tool` 人工验收

## 2. 当前模型配置

当前项目支持两类 provider：

- `mock`：本地开发和测试模式，不调用真实模型。
- `openai_compatible`：真实模型接入模式，使用 OpenAI-compatible API 形式调用 LLM 和 Embedding。

当前人工验收阶段使用：

- LLM：DeepSeek，走 `LLM_PROVIDER=openai_compatible`
- Embedding：智谱 `embedding-3`，走 `EMBEDDING_PROVIDER=openai_compatible`
- Vector Store：Chroma，本地持久化目录 `data/chroma_db`
- Database：SQLite，本地数据库 `data/app.db`

## 3. .env 配置说明

示例配置项如下，真实 key 只写在本地 `.env`，不要提交到仓库。

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
LLM_TIMEOUT_SECONDS=60

EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://your-zhipu-compatible-endpoint/v1
EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_MODEL=embedding-3
EMBEDDING_TIMEOUT_SECONDS=30
```

本地测试或 pytest 骨架建议使用：

```env
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=mock
```

## 4. 切换 embedding 后必须清空数据的原因

切换 embedding 模型后，必须清空：

```text
data/chroma_db
data/app.db
```

原因是不同 embedding 模型生成的向量不在同一个向量空间里。

如果旧文档是用 mock embedding 或其他 embedding 模型入库，而提问时使用智谱 `embedding-3` 生成 query embedding，那么 query 向量和文档 chunk 向量不具备可比较性，检索结果会失真。

因此只要切换以下任意配置，都应该清空旧索引并重新上传文档：

- `EMBEDDING_PROVIDER`
- `EMBEDDING_MODEL`
- `EMBEDDING_BASE_URL` 指向的实际模型服务

## 5. 已完成验证

已完成的人工验证：

- `/documents/upload` 可以上传文档并完成入库
- DeepSeek LLM 可以生成回答
- 智谱 `embedding-3` 可以生成向量并写入 Chroma
- `/chat` 可以基于已上传文档返回 `answer + sources`
- 文档外问题可以拒答或提示资料不足
- `/agent/chat` 可以完成 intent 路由和 tool 调用
- `rag_tool` 可调用 RAGService
- `summary_tool` 可完成总结任务
- `writing_tool` 可完成写作任务
- `general_chat_tool` 可处理普通问答

## 6. 当前主线接口

当前主线接口：

```text
GET  /health
POST /documents/upload
POST /chat
POST /agent/chat
```

开发或实验接口：

```text
POST /documents/index
POST /agent/graph-chat
```

其中 `/documents/index` 和 `/agent/graph-chat` 不作为主线展示接口。

## 7. 当前项目能力总结

当前项目已经具备一个作品级 RAG Agent 后端的最小闭环：

- 支持用户上传企业文档
- 支持文档清洗、chunk、embedding、向量入库
- 支持基于知识库的 RAG 问答
- 支持返回 answer 和 sources
- 支持 chat_logs 记录
- 支持 Agent Router 判断 intent
- 支持 Agent Executor 调用不同 tool
- 支持 mock 模式下的基础测试骨架
- 支持真实 LLM 与真实 Embedding 的 OpenAI-compatible 接入

## 8. 当前仍需优化

后续仍建议优化：

- 自动化测试覆盖率仍较低，目前只是最小 pytest 骨架
- README 仍可在后续整理，但本阶段不做大改
- 中文历史文档和部分旧 prompt 存在编码展示问题
- 上传文件大小限制、重复文档处理、文档删除与重建索引仍未产品化
- `MIN_RELEVANCE_SCORE` 后续可接入检索过滤
- feedback 表已有模型，但反馈 API 和分析链路尚未完成
- eval 自动评估尚未实现

## 9. 下一阶段任务

建议下一阶段聚焦：

1. 补齐 pytest：health、upload、chat、agent、router 的稳定自动化测试。
2. 补 feedback API：允许用户对回答打分和写评论。
3. 补基础 eval：用固定问题集检查 answer 与 sources。
4. 优化检索质量：启用 relevance threshold，必要时增加 rerank。
5. 整理展示文档：README、架构图、接口示例、面试讲解稿。
