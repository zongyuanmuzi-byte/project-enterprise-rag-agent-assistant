# Eval 自动评估计划

生成日期：2026-05-28

## 1. eval 的目的

`eval/` 目录用于保存轻量级手动评估脚本，帮助在每次调整 RAG、Agent Router、Prompt 或模型配置后快速检查主线能力是否退化。

当前 eval 不是严格的自动化评测平台，也不替代人工验收；它是一个作品级后端项目中的最小质量检查工具。

## 2. eval_dataset 字段说明

文件：

```text
eval/eval_dataset.json
```

字段：

- `id`：测试用例唯一标识。
- `question`：要发送给 `/agent/chat` 的问题。
- `expected_tool`：期望 Agent 调用的 tool，例如 `rag_tool`。
- `expected_behavior`：期望行为。
  - `answer_with_sources`：应返回答案且 sources 非空。
  - `no_answer`：应拒答，sources 为空。
  - `no_sources`：非 RAG 工具应不返回 sources。
- `expected_keywords`：答案中期望出现的关键词。

## 3. run_eval.py 使用方法

先启动后端服务：

```bash
uvicorn app.main:app --reload
```

确保已经通过 `/documents/upload` 上传测试文档，并完成 Chroma 入库。

运行默认评估：

```bash
python eval/run_eval.py
```

指定 base_url：

```bash
python eval/run_eval.py --base-url http://127.0.0.1:8000
```

指定数据集：

```bash
python eval/run_eval.py --dataset eval/eval_dataset.json
```

## 4. 当前评估覆盖范围

当前覆盖：

- RAG 文档内问题：退款周期、客服响应时间。
- RAG 文档外问题：CEO 生日。
- Summary tool。
- Writing tool。
- General chat tool。
- Tool routing 是否符合预期。
- RAG sources 是否符合预期。

## 5. 当前限制

- 当前 eval 依赖本地 API 服务已启动。
- 当前 eval 依赖知识库中已上传合适的测试文档。
- 当前关键词匹配是简单字符串包含，不做语义评分。
- LLM 输出有随机性，真实模型可能表达不同，关键词需要随提示词和文档内容调优。
- 当前不依赖 pytest，不纳入严格 CI。
