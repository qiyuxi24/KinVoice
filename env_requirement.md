# 家语 AI - 环境依赖与配置方法（完整版）

## 一、前端环境（快应用原生）

### 1.1 基础软件

- Node.js 24.24
- hap-toolkit: `npm install -g hap-toolkit`
- 快应用调试器 APK（从vivo开放平台下载，安装到Android手机）

### 1.2 项目依赖（`frontend/package.json`）

```json
{
  "name": "jiayu-quickapp",
  "version": "1.0.0",
  "devDependencies": {
    "hap-toolkit": "^0.0.46"
  },
  "scripts": {
    "dev": "hap watch",
    "build": "hap build",
    "server": "hap server"
  }
}
```

### 1.3 配置验证

```bash
cd frontend
hap -v          # 显示版本号
hap init test   # 测试创建项目
```

***

## 二、后端环境（FastAPI + Python）

### 2.1 系统要求

- Python 3.11
- PostgreSQL 15+ 并启用 pgvector 扩展
- Redis 7+（可选，但推荐）

### 2.2 Python 依赖清单（`backend/requirements.txt`）

```text
# 核心框架
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-dotenv==1.0.0

# 数据库与ORM
sqlalchemy==2.0.30
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.0
redis==5.0.1

# AI与向量检索
httpx==0.27.0
sentence-transformers==2.2.2

# 语音合成（二选一，以Azure为例）
azure-cognitiveservices-speech==1.36.0

# 工具类
pydantic==2.7.0
pydantic-settings==2.2.0
python-multipart==0.0.9
loguru==0.7.2

# 开发与测试
pytest==8.0.0
pytest-asyncio==0.23.0
black==24.0.0
```

### 2.3 PostgreSQL + pgvector 安装

#### Docker（推荐）

```bash
docker run -d --name jiayu-postgres \
  -e POSTGRES_DB=jiayu_ai \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -p 5432:5432 \
  pgvector/pgvector:pg15
```

#### 手动（Ubuntu）

```bash
sudo apt install postgresql-15 postgresql-15-pgvector
sudo -u postgres psql -c "CREATE DATABASE jiayu_ai;"
sudo -u postgres psql -d jiayu_ai -c "CREATE EXTENSION vector;"
```

### 2.4 Redis 安装（可选）

```bash
docker run -d --name jiayu-redis -p 6379:6379 redis:7-alpine
```

### 2.5 环境变量配置（`backend/.env`）

```ini
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/jiayu_ai
REDIS_URL=redis://localhost:6379/0
LLM_API_KEY=your_key_here
LLM_API_BASE=https://openapi.vivo.com/xxx
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=eastasia
EMBEDDING_CACHE_DIR=../data/embedding_cache
```

### 2.6 后端安装与启动

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

***

## 三、Docker Compose 全栈启动（可选）

创建 `backend/docker-compose.yml`：

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: jiayu_ai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  backend:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    env_file:
      - .env
volumes:
  pgdata:
```

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /app/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

启动：`docker-compose up -d`

***

## 四、常见问题

1. **hap命令找不到**：重新安装 `npm install -g hap-toolkit` 或检查Node.js环境变量。
2. **pgvector扩展未启用**：使用Docker镜像 `pgvector/pgvector` 已预装；手动安装需执行 `CREATE EXTENSION vector;`。
3. **sentence-transformers下载慢**：手动下载模型 `all-MiniLM-L6-v2` 放到 `EMBEDDING_CACHE_DIR` 目录，或设置环境变量 `TRANSFORMERS_CACHE`。
4. **Azure TTS认证失败**：检查 `.env` 中的密钥和区域是否正确，且账户有效。

> 更新日期：2026-05-27 | 维护：家语AI团队

```
```

