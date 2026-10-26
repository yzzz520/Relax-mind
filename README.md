# AI 情绪胶囊

基于 Vue 3、Vite、Pinia、Vue Router、ECharts 与 html2canvas 的前端原型。情绪分析、音乐匹配和账户数据当前均由本地 mock 提供，不连接真实后端。

## 本地开发

```bash
npm install
npm run dev
```

生产构建：

```bash
npm run build
```

## 开发脚本

- `node scripts/test-pick-music.mjs`：验证同一文本选曲稳定、同象限文本能产生不同曲目，并抽查四象限判定。分布测试需按 `docs/S3-下-补充-曲库.md` §8 临时加入 `calm-2`、`calm-3`，验证后删除。

## 音频素材

`public/audio/` 中的曲目为开发占位素材，授权状态未确认，不应作为公共领域素材分发。

## Backend Batch A

后端位于 `backend/`，当前包含 FastAPI 骨架、JWT 登录、本地曲库与 Mock 情绪分析。

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

接口文档：`http://127.0.0.1:8000/docs`。

当前使用 `Base.metadata.create_all()` 建表。上线前需要迁移到 Alembic。

### LLM analyzer

批次 B 使用 OpenAI 兼容的 Chat Completions 接口。配置以下变量后重启服务：

```dotenv
MOOD_ANALYZER=llm
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=your-key
LLM_MODEL=deepseek-flash
LLM_TIMEOUT_SECONDS=30
```

每次 LLM 调用都会记录 `duration_ms`。HTTP 状态、超时、JSON 解析和结构校验失败会记录 WARNING，并回退到 Mock 分析器。`GET /api/health` 的 `analyzer` 字段显示当前实际状态：`llm` 或 `mock-fallback`。

## Supabase frontend

前端 Supabase client 固定使用同源 `${window.location.origin}/sb`，开发代理目标来自 `VITE_SUPABASE_TARGET_URL`。本机无法访问 `*.supabase.co`，本地演示请使用：

```dotenv
VITE_DATA_MODE=mock
```

API 模式通过 Supabase Auth 登录，并将情绪胶囊写入 `capsules` 表。曲库始终同步读取 `src/data/musicLibrary.js`，不依赖数据库。

## Vercel Serverless API

`vercel.json` 将 `/sb/*` 转发到 Supabase，并明确注册 `api/analyze.py`、`api/health.py` 两个 Python 函数。

Vercel 环境变量：

```text
SUPABASE_JWT_SECRET
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

不要把服务端变量加 `VITE_` 前缀。`POST /api/analyze` 必须携带 Supabase 用户 JWT；`GET /api/health` 返回当前配置下生效的 analyzer 状态。
