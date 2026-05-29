# 阶段 1：工程底座

## 1. 本阶段目标

本阶段目标是把 Enterprise RAG Agent Assistant 从一个普通 demo 搭建成一个标准、清晰、可扩展的 FastAPI AI 应用工程骨架。

本阶段不追求复杂 AI 功能，而是重点完成项目结构、配置管理、SQLite 数据库、SQLAlchemy ORM、日志、异常处理和 Docker 运行。

## 2. 完成的功能

- 创建标准 FastAPI 项目目录结构
- 实现 GET /health 健康检查接口
- 实现 POST /chat 基础聊天接口
- 使用 Pydantic 定义 ChatRequest、ChatResponse、ErrorResponse
- 使用 pydantic-settings 读取 .env 配置
- 使用 SQLite + SQLAlchemy ORM 创建数据库
- 创建 documents、chunks、chat_logs、feedback 四张表
- POST /chat 后写入 chat_logs
- 使用 Python logging 记录请求日志
- 实现基础异常处理
- 编写 Dockerfile 和 .dockerignore
- 完成本地运行和 Docker 运行验证

## 3. 新增文件和目录

```text
app/main.py
app/config.py
app/schemas.py
app/api/health.py
app/api/chat.py
app/services/chat_service.py
app/database/db.py
app/database/models.py
app/utils/logger.py
requirements.txt
Dockerfile
.dockerignore
.env.example
.gitignore
README.md
00_project_notes/stage_01_engineering_foundation.md
