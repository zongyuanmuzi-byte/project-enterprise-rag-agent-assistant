# 企业 RAG Agent 助手前端

这是“企业 RAG Agent 助手”的单页演示前端，用于展示后端企业知识库 RAG + Agent 能力。

本前端用于作品展示和面试演示，不包含登录、路由、部署、聊天历史等复杂功能。

## 1. 前端作用

当前界面展示以下能力：

- 后端健康检查
- 企业文档上传
- 通过 `/chat` 进行 RAG 问答
- 通过 `/agent/chat` 进行 Agent 问答
- 展示回答来源 sources
- 根据后端是否返回 `chat_log_id` 展示反馈表单或占位提示

## 2. 安装依赖

```bash
cd frontend
npm install
```

## 3. 配置后端地址

从示例文件创建本地 `.env`：

```bash
cp .env.example .env
```

Docker 后端统一映射到本机 `8010`，推荐配置为：

```env
VITE_API_BASE_URL=http://localhost:8010
```

修改 `.env` 后需要重启 `npm run dev`，Vite 才会重新读取环境变量。

如果没有配置 `.env`，前端代码会默认请求 `http://localhost:8010`。

## 4. 启动开发服务

```bash
npm run dev
```

打开终端显示的 Vite 地址，通常是：

```text
http://localhost:5173
```

## 5. 使用的后端接口

- `GET /health`
- `POST /documents/upload`
- `POST /chat`
- `POST /agent/chat`
- `POST /feedback`

## 6. 当前限制

- 没有登录或用户管理。
- 没有前端路由。
- 没有聊天历史。
- 只有后端响应包含 `chat_log_id` 时才能提交反馈。
- 默认假设 FastAPI 后端已经启动。
- 本地联调默认直接请求 `http://localhost:8010`，后端需要允许 `http://localhost:5173` 跨域访问。
