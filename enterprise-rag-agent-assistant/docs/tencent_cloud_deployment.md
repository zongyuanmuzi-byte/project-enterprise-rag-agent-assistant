# 腾讯云生产化模拟部署说明

## 1. 部署目标

本项目的腾讯云主线目标架构如下：

```text
CloudBase 静态网站托管 React 前端
↓
CloudBase 云托管 FastAPI 后端
↓
腾讯云 COS 保存上传文件
↓
腾讯云 MySQL 保存 documents / chunks / chat_logs / feedback
↓
腾讯云 VectorDB 保存 chunk embeddings
↓
DeepSeek LLM + 智谱 embedding-3
```

这条路线用于真实生产流程模拟：把本地 SQLite、本地 `data/uploads`、本地 Chroma 逐步替换为云数据库、对象存储和托管向量数据库。

## 2. 重要提醒

Enterprise RAG Agent Assistant 是 production-minded portfolio project，不是完整 production-ready SaaS。

第一版腾讯云部署用于学习真实生产流程，包括环境变量、CORS、对象存储、云数据库、向量数据库、日志和成本控制。

开通 MySQL、VectorDB、COS 前必须先查看费用、免费额度、地域、规格和是否自动续费。

不要把真实 API key、COS Secret、数据库密码或 VectorDB 密钥提交到 GitHub。

## 3. 腾讯云资源准备清单

- CloudBase 环境
- CloudBase 云托管服务
- CloudBase 静态网站托管
- COS Bucket
- 云数据库 MySQL 实例
- VectorDB 实例
- DeepSeek API Key
- Zhipu Embedding API Key

## 4. 后端环境变量清单

```env
APP_ENV=production
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname?charset=utf8mb4
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-frontend-domain

LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
LLM_API_KEY=your_deepseek_api_key

EMBEDDING_PROVIDER=openai_compatible
EMBEDDING_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
EMBEDDING_MODEL=embedding-3
EMBEDDING_API_KEY=your_zhipu_api_key

STORAGE_PROVIDER=cos
COS_SECRET_ID=your_cos_secret_id
COS_SECRET_KEY=your_cos_secret_key
COS_BUCKET=your_bucket_name
COS_REGION=ap-guangzhou
COS_PREFIX=uploads/

VECTOR_STORE_PROVIDER=tencent_vectordb
TENCENT_VECTORDB_URL=your_vectordb_url
TENCENT_VECTORDB_API_KEY=your_vectordb_api_key
TENCENT_VECTORDB_USERNAME=your_vectordb_username
TENCENT_VECTORDB_PASSWORD=your_vectordb_password
TENCENT_VECTORDB_DATABASE=your_vectordb_database
TENCENT_VECTORDB_COLLECTION=enterprise_rag_chunks
TENCENT_VECTORDB_DIMENSION=2048
```

说明：当前代码已经准备了 `VECTOR_STORE_PROVIDER=tencent_vectordb` 的适配边界，但腾讯云 VectorDB SDK/API 调用仍需根据官方文档补全。未补全前不要在真实环境启用该 provider。

## 5. 前端环境变量

```env
VITE_API_BASE_URL=https://your-backend-domain
```

前端构建产物会把该地址写入浏览器代码中。上线前必须确认它不是 `localhost`。

## 6. 部署顺序

第一步：本地验证 local 模式。

```bash
docker compose down
docker compose up --build
```

第二步：创建腾讯云资源，包括 CloudBase、COS、MySQL、VectorDB。

第三步：配置 MySQL，创建数据库、账号、密码、网络访问规则，并准备 `DATABASE_URL`。

第四步：配置 COS，创建 Bucket，确认 Region、Bucket 名称、SecretId、SecretKey 和最小权限。

第五步：配置 VectorDB，创建 database / collection，并确认 collection 维度为 `2048`，需要和智谱 `embedding-3` 向量维度一致。

第六步：部署 CloudBase 后端，设置后端环境变量，确认容器监听端口符合 CloudBase 云托管要求。

第七步：获取后端 URL，并访问 `/health` 验证后端可用。

第八步：配置前端 `VITE_API_BASE_URL=https://your-backend-domain`。

第九步：部署 CloudBase 静态网站托管，上传或发布 React 构建产物。

第十步：回到后端更新 `CORS_ORIGINS=https://your-frontend-domain`。

第十一步：线上完整验收。

## 7. 线上验收清单

- 后端 `/health` 可访问
- 前端页面可访问
- 前端 Health Check 成功
- Console 无 CORS error
- Network 请求指向线上后端
- 上传文档成功
- 文件进入 COS
- `documents` / `chunks` 写入 MySQL
- embeddings 写入 VectorDB
- RAG 问答成功
- Agent 问答成功
- sources 正常显示
- 文档外问题能拒答

## 8. 常见错误排查

- CloudBase 容器端口不对：确认 FastAPI 监听 `0.0.0.0`，端口和平台配置一致。
- 前端仍请求 localhost：检查前端构建时的 `VITE_API_BASE_URL`。
- CORS_ORIGINS 没有包含前端域名：在后端环境变量中加入正式前端域名，并重启后端。
- COS Secret / Bucket / Region 错误：确认 Secret 权限、Bucket 名称和 Region 完全匹配。
- MySQL 白名单 / 网络 / 账号密码错误：确认云托管服务能访问数据库，账号有建表和读写权限。
- VectorDB collection 维度和 embedding 维度不一致：智谱 `embedding-3` 当前按 `2048` 规划，collection 必须匹配。
- API key 缺失：检查 DeepSeek、智谱、COS、VectorDB 相关环境变量。
- SQLite 和 MySQL 切换后旧数据不可用：SQLite 本地数据不会自动进入 MySQL，初版云环境建议新库启动并重新上传文档。
- Chroma 和 VectorDB 不能混用向量空间：切换向量库或 embedding 模型后需要重新入库。

## 9. 成本控制

- 开通资源前先看计费方式、免费额度和自动续费设置。
- 选择最低规格验证流程。
- 测试后及时关闭不用资源。
- API key 设置额度、限流或费用告警。
- COS 注意外网流量费用、请求次数费用和存储费用。
- MySQL 注意实例费用、存储费用和备份费用。
- VectorDB 注意实例规格、空闲费用和最低计费单位。
- 首次部署先跑通最小闭环，不要一次性购买高规格资源。
