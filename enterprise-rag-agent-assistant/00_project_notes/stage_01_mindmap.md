# 阶段 1：工程底座思维导图

```mermaid
mindmap
  root((阶段 1：工程底座))
    阶段目标
      从 demo 变成工程项目
      建立 FastAPI 后端骨架
      为 RAG 和 Agent 做准备
      可运行
      可记录
      可部署
      可扩展

    项目结构
      app
        main.py
          应用入口
          注册路由
          初始化数据库
          全局异常处理
        config.py
          读取 env
          管理配置
          校验配置
        schemas.py
          API 请求模型
          API 响应模型
          数据校验
      api
        health.py
          GET /health
          服务健康检查
        chat.py
          POST /chat
          接收问题
          调用 service
          返回响应
      services
        chat_service.py
          业务逻辑
          生成 request_id
          生成 placeholder answer
          计算 latency
          写入 chat_logs
      database
        db.py
          engine
          SessionLocal
          Base
          get_db
          init_db
        models.py
          documents
          chunks
          chat_logs
          feedback
      utils
        logger.py
          logging
          LOG_LEVEL
          request_id
          latency_ms
          error_message
      prompts
        后续 RAG prompt
        后续 Agent prompt
      tools
        后续 Agent tools

    配置管理
      .env.example
        公开配置模板
        可提交 GitHub
      .env
        本地真实配置
        不提交 GitHub
      APP_NAME
      APP_ENV
        development
        production
      DATABASE_URL
        sqlite:///./data/app.db
      LLM_PROVIDER
        placeholder
      LLM_API_KEY
        后续接 LLM
      LOG_LEVEL
        INFO
        DEBUG
        ERROR

    数据库
      SQLite
        本地文件数据库
        data/app.db
        适合开发阶段
      SQLAlchemy
        ORM 工具
        Python 类映射数据库表
      db.py
        engine
          连接数据库
        SessionLocal
          创建数据库会话
        Base
          ORM 模型基类
        get_db
          每次请求提供 db session
        init_db
          自动创建表
      models.py
        Document
          documents 表
          存文档元信息
        Chunk
          chunks 表
          存文档切分内容
        ChatLog
          chat_logs 表
          存问答记录
        Feedback
          feedback 表
          存用户反馈

    API
      GET /health
        检查服务是否运行
        返回 status ok
      POST /chat
        请求
          question
        响应
          answer
          request_id
          latency_ms
        当前阶段
          placeholder answer
        下一阶段
          RAG answer
          sources

    Pydantic
      ChatRequest
        question
        防止空问题
      ChatResponse
        answer
        request_id
        latency_ms
      ErrorResponse
        detail
        request_id
      作用
        校验请求
        规范响应
        自动生成 Swagger 文档

    日志系统
      Python logging
      app_logger
      LOG_LEVEL 控制
      记录内容
        request_id
        question
        latency_ms
        error_message
      作用
        排查错误
        追踪请求
        面试体现工程意识

    异常处理
      空 question
        Pydantic 拦截
      数据库写入失败
        SQLAlchemyError
        rollback
      未知异常
        Exception
      统一返回格式
        detail
        request_id

    Docker
      Dockerfile
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt
        RUN pip install
        COPY .
        EXPOSE 8000
        CMD uvicorn
      .dockerignore
        忽略 .venv
        忽略 .env
        忽略 data/*.db
      image
        应用运行模板
      container
        image 运行实例
      端口映射
        -p 8000:8000
        本机端口:容器端口
      环境变量
        --env-file .env
      访问
        localhost:8000/docs

    验证结果
      本地运行
        uvicorn app.main:app --reload
      Swagger
        /docs 可打开
      health
        返回 ok
      chat
        返回 answer request_id latency_ms
      数据库
        自动创建四张表
        chat_logs 有记录
      Docker
        build 成功
        run 成功
        docs 可打开

    常见错误
      ModuleNotFoundError
        不在项目根目录
      .venv broken
        VS Code 没选 WSL 解释器
      Address already in use
        8000 端口被占用
      Docker not found in WSL
        没开 WSL Integration
      /chat 422
        请求体格式错误
      localhost 访问错端口
        看 -p 本机端口

    README 和简历
      README
        项目简介
        当前功能
        运行方式
        API 示例
        下一阶段计划
      简历中文
        FastAPI 工程骨架
        SQLAlchemy SQLite
        日志与异常处理
        Docker 部署
      简历英文
        FastAPI backend foundation
        layered architecture
        SQLAlchemy ORM
        logging and error handling
        Dockerized deployment

    下一阶段
      阶段 2：RAG 核心作品
        文档加载
        文本清洗
        chunk 切分
        embedding
        向量存储
        topK 检索
        RAG prompt
        answer + sources
        替换 placeholder answer