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
