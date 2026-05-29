from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_FILE = PROJECT_ROOT / "00_project_notes" / "current_code_summary.md"

INCLUDE_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".env",
    ".example",
    ".dockerignore",
    ".gitignore",
}

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "data/chroma_db",
}

EXCLUDE_FILES = {
    "data/app.db",
}


def should_skip_path(path: Path) -> bool:
    """
    判断某个路径是否应该跳过。

    这里会跳过：
    1. 虚拟环境
    2. Git 目录
    3. Python 缓存
    4. Chroma 向量库数据
    5. SQLite 数据库文件
    """
    relative_path = path.relative_to(PROJECT_ROOT).as_posix()

    for exclude_dir in EXCLUDE_DIRS:
        if relative_path == exclude_dir or relative_path.startswith(exclude_dir + "/"):
            return True

    if relative_path in EXCLUDE_FILES:
        return True

    if path.name.endswith(".pyc"):
        return True

    return False


def collect_files() -> list[Path]:
    """
    收集项目中需要总结的文件。
    """
    files: list[Path] = []

    for path in PROJECT_ROOT.rglob("*"):
        if should_skip_path(path):
            continue

        if path.is_file():
            if path.suffix in INCLUDE_EXTENSIONS or path.name in {
                "Dockerfile",
                "requirements.txt",
                "README.md",
                ".env.example",
                ".gitignore",
                ".dockerignore",
            }:
                files.append(path)

    return sorted(files, key=lambda p: p.relative_to(PROJECT_ROOT).as_posix())


def build_project_tree(files: list[Path]) -> str:
    """
    根据收集到的文件生成简化项目树。
    """
    lines = []

    for file_path in files:
        relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        lines.append(relative_path)

    return "\n".join(lines)


def read_file_content(file_path: Path) -> str:
    """
    安全读取文件内容。
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "[无法用 UTF-8 读取该文件]"
    except Exception as exc:
        return f"[读取文件失败: {exc}]"


def detect_file_role(relative_path: str) -> str:
    """
    根据文件路径判断它在项目中的作用。
    """
    role_map = {
        "app/main.py": "FastAPI 应用入口，负责创建 app、初始化数据库、注册路由和全局异常处理。",
        "app/config.py": "配置管理文件，负责读取 .env 中的项目配置、RAG 配置、Embedding 配置和 LLM 配置。",
        "app/schemas.py": "Pydantic 数据模型文件，定义 API 请求和响应结构。",
        "app/api/health.py": "健康检查接口。",
        "app/api/chat.py": "RAG 问答接口入口。",
        "app/api/documents.py": "文档索引接口入口。",
        "app/database/db.py": "数据库连接、Session 管理和数据库初始化。",
        "app/database/models.py": "SQLAlchemy ORM 模型，定义 documents、chunks、chat_logs、feedback 表。",
        "app/services/document_service.py": "文档处理服务，负责读取、清洗、切分、写入 SQL，并完成 RAG 索引。",
        "app/services/embedding_service.py": "Embedding 客户端封装，支持 mock 和 OpenAI-compatible 结构。",
        "app/services/vector_store_service.py": "Chroma 向量库服务，负责写入 chunks 和相似度检索。",
        "app/services/rag_service.py": "RAG 问答主流程服务，串联 embedding、向量检索、prompt、LLM 和 chat_logs。",
        "app/services/llm_service.py": "LLM 客户端封装，支持 mock 和 OpenAI-compatible 结构。",
        "app/prompts/rag_prompt.py": "RAG Prompt 构造文件，负责生成基于 context 和 question 的提示词。",
        "app/utils/logger.py": "日志工具文件，统一创建 logger。",
        "README.md": "项目说明文档。",
        "requirements.txt": "Python 依赖文件。",
        "Dockerfile": "Docker 镜像构建文件。",
        ".env.example": "环境变量示例文件。",
        "tests/rag_eval_questions.md": "RAG 人工评测问题集。",
    }

    return role_map.get(relative_path, "项目文件。")


def get_markdown_language(file_path: Path) -> str:
    """
    根据文件类型返回 Markdown 代码块语言。
    """
    suffix = file_path.suffix

    if suffix == ".py":
        return "python"

    if suffix == ".md":
        return "markdown"

    if suffix in {".env", ".example"} or file_path.name == ".env.example":
        return "env"

    if file_path.name == "Dockerfile":
        return "dockerfile"

    if suffix == ".txt":
        return "text"

    return "text"


def build_summary(files: list[Path]) -> str:
    """
    生成完整 Markdown 总结内容。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    project_tree = build_project_tree(files)

    lines = []

    lines.append("# 当前项目代码总结")
    lines.append("")
    lines.append(f"生成时间：{now}")
    lines.append("")
    lines.append("项目名称：Enterprise RAG Agent Assistant")
    lines.append("")
    lines.append("当前阶段：阶段 2：RAG 核心作品")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 1. 项目当前状态")
    lines.append("")
    lines.append("当前项目已经从基础 FastAPI 工程升级为一个最小可运行的企业知识库 RAG 问答系统。")
    lines.append("")
    lines.append("当前已具备：")
    lines.append("")
    lines.append("- FastAPI 后端项目结构")
    lines.append("- SQLite + SQLAlchemy 数据库")
    lines.append("- documents、chunks、chat_logs、feedback 表")
    lines.append("- 文档读取、清洗、chunk 切分")
    lines.append("- 文档和 chunks 写入 SQLite")
    lines.append("- EmbeddingClient 封装")
    lines.append("- Chroma 向量库服务")
    lines.append("- 文档索引接口 `/documents/index`")
    lines.append("- RAG Prompt")
    lines.append("- LLMClient 封装")
    lines.append("- RAG 问答接口 `/chat`")
    lines.append("- answer + sources 返回")
    lines.append("- chat_logs 问答日志记录")
    lines.append("- RAG 人工评测问题集")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 2. 当前项目文件树")
    lines.append("")
    lines.append("```text")
    lines.append(project_tree)
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 3. 核心文件作用说明")
    lines.append("")

    for file_path in files:
        relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        role = detect_file_role(relative_path)

        lines.append(f"### `{relative_path}`")
        lines.append("")
        lines.append(role)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. RAG 主流程总结")
    lines.append("")
    lines.append("### 4.1 文档索引流程")
    lines.append("")
    lines.append("```text")
    lines.append("本地 .txt / .md 文档")
    lines.append("↓")
    lines.append("read_file() 读取文件")
    lines.append("↓")
    lines.append("clean_text() 清洗文本")
    lines.append("↓")
    lines.append("split_text() 切分 chunks")
    lines.append("↓")
    lines.append("documents / chunks 写入 SQLite")
    lines.append("↓")
    lines.append("EmbeddingClient 生成 chunk embeddings")
    lines.append("↓")
    lines.append("VectorStoreService 写入 Chroma")
    lines.append("```")
    lines.append("")

    lines.append("### 4.2 RAG 问答流程")
    lines.append("")
    lines.append("```text")
    lines.append("用户问题")
    lines.append("↓")
    lines.append("EmbeddingClient 生成 question embedding")
    lines.append("↓")
    lines.append("VectorStoreService 从 Chroma 检索 top-k chunks")
    lines.append("↓")
    lines.append("build_context_from_chunks() 拼接 context")
    lines.append("↓")
    lines.append("build_rag_prompt() 构造 RAG prompt")
    lines.append("↓")
    lines.append("LLMClient 生成 answer")
    lines.append("↓")
    lines.append("返回 answer + sources")
    lines.append("↓")
    lines.append("写入 chat_logs")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 5. 当前代码全文快照")
    lines.append("")
    lines.append("下面是当前项目主要代码文件内容，用于迁移到新会话、复盘学习和让 AI 继续理解项目状态。")
    lines.append("")

    for file_path in files:
        relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()
        language = get_markdown_language(file_path)
        content = read_file_content(file_path)

        lines.append(f"### FILE: `{relative_path}`")
        lines.append("")
        lines.append(f"```{language}")
        lines.append(content)
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 6. 下一步建议")
    lines.append("")
    lines.append("当前阶段 2 的 RAG 核心链路已经基本完成。")
    lines.append("")
    lines.append("下一阶段建议进入：")
    lines.append("")
    lines.append("```text")
    lines.append("阶段 3：Agent / 工作流增强")
    lines.append("```")
    lines.append("")
    lines.append("重点包括：")
    lines.append("")
    lines.append("- 用户意图分类")
    lines.append("- 将 RAG 封装为 tool")
    lines.append("- 简单工具路由")
    lines.append("- 普通聊天 / RAG 问答 / 文档管理的任务分流")
    lines.append("- LangGraph 基础实践")
    lines.append("- 文档更新和删除流程")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    files = collect_files()
    summary = build_summary(files)

    OUTPUT_FILE.write_text(summary, encoding="utf-8")

    print(f"代码总结文件已生成: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")
    print(f"共收集文件数量: {len(files)}")


if __name__ == "__main__":
    main()