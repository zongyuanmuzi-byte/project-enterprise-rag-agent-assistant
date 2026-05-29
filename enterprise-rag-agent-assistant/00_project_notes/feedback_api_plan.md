# Feedback API 计划与实现记录

生成日期：2026-05-28

## 1. 为什么需要 feedback

RAG 系统需要持续知道回答是否有用、是否引用了正确资料、是否存在幻觉或检索错误。

`feedback` 的作用是让用户或测试人员对某一次 `chat_logs` 记录进行评分和备注，为后续优化提供数据依据。

## 2. feedback 和 chat_logs 的关系

当前数据库中已有：

- `chat_logs`：保存每次问答的 question、answer、tool_used、retrieved_chunks、latency、error_message。
- `feedback`：保存用户对某条 chat log 的 rating 和 comment。

关系：

```text
chat_logs.id
↓
feedback.chat_log_id
```

一条 chat log 可以关联多条 feedback 记录。

## 3. POST /feedback 请求和响应

接口：

```text
POST /feedback
```

请求示例：

```json
{
  "chat_log_id": 1,
  "rating": 1,
  "comment": "答案没有引用正确政策"
}
```

字段说明：

- `chat_log_id`：必填，必须对应已有 chat log。
- `rating`：必填，范围 1 到 5。
- `comment`：可选，用户备注。

响应示例：

```json
{
  "feedback_id": 1,
  "chat_log_id": 1,
  "rating": 1,
  "comment": "答案没有引用正确政策",
  "status": "created"
}
```

如果 `chat_log_id` 不存在，接口返回友好错误。

## 4. 当前限制

- 当前只支持创建 feedback，不支持查询、更新、删除 feedback。
- 当前 rating 只是简单 1 到 5 分，没有更细的分类标签。
- 当前 feedback 尚未接入自动 eval 或模型优化流程。

## 5. 后续如何用于 eval 和优化

后续可以基于 feedback 做：

- 统计低分问题。
- 定位检索失败或答案不准确的 case。
- 反向补充 eval_dataset。
- 调整 chunk_size、chunk_overlap、MIN_RELEVANCE_SCORE。
- 优化 prompt 或 Agent Router 分类规则。
- 在后续版本中形成“人工反馈 -> eval case -> RAG 优化”的闭环。
