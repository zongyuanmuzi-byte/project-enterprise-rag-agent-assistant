# 面试展示脚本

本文档是一份面试或项目演示时可参考的讲解脚本。

## 1. 项目介绍

大家好，这是我的 Enterprise RAG Agent Assistant 项目。

这是一个企业知识库 RAG + Agent 后端系统，基于 FastAPI 构建。它支持上传企业内部文档，把文档解析、清洗、切分后写入 SQLite 和 Chroma，然后通过 DeepSeek LLM 和智谱 `embedding-3` 实现基于知识库的问答。

项目还实现了一个轻量 Agent 调度层：`AgentRouter` 负责判断用户意图，`ToolExecutor` 负责调用不同工具，例如知识库问答、总结、写作和普通解释。

这个项目不是 production-ready 产品，而是一个 production-minded portfolio project，重点展示 AI 应用后端的主线工程能力。

## 2. 上传公司政策文档

先启动服务：

```bash
uvicorn app.main:app --reload
```

打开 Swagger：

```text
http://127.0.0.1:8000/docs
```

调用：

```text
POST /documents/upload
```

上传一份公司政策文档，例如 `company_policy.md`。

讲解重点：

- 系统会保存上传文件。
- `document_service` 会读取文档、清洗文本、切分 chunks。
- SQLite 保存文档和 chunk 元数据。
- 智谱 `embedding-3` 生成向量。
- Chroma 保存 chunk embeddings。

## 3. 用 /chat 提问退款周期

调用：

```text
POST /chat
```

示例问题：

```text
公司的退款周期是多久？
```

预期展示：

- 返回 `answer`
- 返回 `sources`
- sources 里包含来源文件、chunk_index、document_id、content、distance

讲解重点：

- `/chat` 是直接 RAG 问答入口。
- 系统会把用户问题转成 query embedding。
- 从 Chroma 检索相关 chunk。
- 把 chunk 拼成 context。
- 调用 DeepSeek 生成回答。
- 返回答案和可追溯来源。

## 4. 用 /chat 提问文档外问题，展示拒答

示例问题：

```text
公司今年年会在哪里举办？
```

如果文档里没有相关信息，系统应拒答或提示资料不足。

讲解重点：

- RAG 系统不应该凭空编造。
- 项目通过 prompt 和检索上下文约束回答。
- 文档外问题不会强行生成看似合理但无来源的答案。

## 5. 用 /agent/chat 测试知识库问答

调用：

```text
POST /agent/chat
```

示例问题：

```text
公司的退款周期是多久？
```

预期：

```text
intent = document_qa
tool_used = rag_tool
sources 非空
```

讲解重点：

- AgentRouter 判断这是企业文档问答。
- ToolExecutor 调用 `rag_tool`。
- `rag_tool` 复用 RAGService。

## 6. 用 /agent/chat 测试总结任务

示例问题：

```text
请总结下面这段话：客户退款需要先审核，再由财务处理。
```

预期：

```text
intent = summary
tool_used = summary_tool
sources = []
```

讲解重点：

- 总结任务不需要查知识库。
- 非 RAG 工具不返回 sources。

## 7. 用 /agent/chat 测试写作任务

示例问题：

```text
帮我写一封英文邮件，告诉客户我们已经收到退款申请。
```

预期：

```text
intent = writing
tool_used = writing_tool
sources = []
```

讲解重点：

- 写作任务由 writing tool 处理。
- 该工具调用 LLM 生成内容，但不走向量检索。

## 8. 用 /agent/chat 测试普通解释任务

示例问题：

```text
请用简单的话解释什么是 RAG。
```

预期：

```text
intent = general_chat
tool_used = general_chat_tool
sources = []
```

讲解重点：

- 普通概念解释不属于企业知识库问答。
- AgentRouter 会将其分发给 general chat 工具。

## 9. 总结项目亮点

演示反馈闭环时，可以补充调用：

```text
POST /feedback
```

示例：

```json
{
  "chat_log_id": 1,
  "rating": 4,
  "comment": "回答有引用来源，基本符合预期。"
}
```

说明：feedback 会关联到 `chat_logs`，后续可以用于 eval case 补充和 RAG 质量优化。

也可以展示轻量 eval：

```bash
python eval/run_eval.py
```

它会读取 `eval/eval_dataset.json`，调用本地 `/agent/chat`，检查 tool、关键词、sources 和 no-answer 行为。

可以这样总结：

这个项目完成了一个企业知识库 RAG + Agent 后端的最小闭环：

- 支持文档上传和入库。
- 支持 SQLite 元数据存储。
- 支持 Chroma 向量检索。
- 接入 DeepSeek LLM 和智谱 `embedding-3`。
- 支持 `/chat` 基础 RAG 问答。
- 支持 `answer + sources` 可追溯回答。
- 支持文档外问题拒答。
- 支持 `/agent/chat` Agent 调度。
- 支持 RAG、总结、写作、普通解释四类工具。
- 支持 feedback 记录和轻量 eval 脚本。

最后可以补一句：

后续我会继续补 feedback、eval、检索质量优化和更完整的自动化测试，让它从作品级后端进一步向真实业务系统靠近。
