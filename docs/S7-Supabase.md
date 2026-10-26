# S7 Supabase 迁移

> 给 Codex 的任务单。**分三批**，每批做完停下报告。
> 目标：认证 + 数据交给 Supabase，FastAPI 只保留 LLM 分析。

---

## 实测网络事实（先读这段）

| 域名 | 国内可达 |
|---|---|
| `supabase.com`（Dashboard / 文档） | ✅ 200 |
| `*.supabase.co`（API） | ❌ ECONNRESET（TLS 阶段被切断） |

**结论**：可以在后台建表、配 RLS，但**前端绝不能直连 `*.supabase.co`**。

---

## 方案 A：用自有域名代理 Supabase API

```
浏览器
  └──→ https://你的域名/sb/*        （同域，无 CORS）
            │
            ├─ 开发时：Vite proxy  →  https://xxx.supabase.co/*   （需开系统代理）
            └─ 生产时：Vercel rewrite → https://xxx.supabase.co/* （服务端发起，不受墙影响）
```

### 实现（三处）

**1. `vercel.json`**

```json
{
  "rewrites": [
    {
      "source": "/sb/:path*",
      "destination": "https://tlsaccyapnfnxxritbbl.supabase.co/:path*"
    }
  ]
}
```

**2. 前端 client 的 URL 用 `/sb`**

```js
// src/lib/supabase.js
const proxyBase = `${window.location.origin}/sb`
export const supabase = createClient(proxyBase, import.meta.env.VITE_SUPABASE_ANON_KEY, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
})
```

> `supabase-js` 会自动在 base 后面拼 `/auth/v1/...` 和 `/rest/v1/...`，
> 所以最终请求是 `https://你的域名/sb/auth/v1/token` → rewrite 后到达 Supabase。

**3. `vite.config.js` 加 dev 代理**

```js
server: {
  proxy: {
    '/sb': {
      target: 'https://tlsaccyapnfnxxritbbl.supabase.co',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/sb/, ''),
    },
  },
},
```

**本地开发的限制（必须知道）**：Vite 的 proxy 跑在你本机，而本机连不上 `supabase.co`。
所以本地要跑真实 Supabase，**必须先开代理软件**；不开代理时用 `VITE_DATA_MODE=mock`。

**生产环境不受此影响**——rewrite 由 Vercel 服务器发起，它在美国，能正常访问 Supabase。

---

## 目标架构

```
浏览器
├──→ Supabase（Auth + Postgres）     前端直连，anon key + RLS
└──→ FastAPI `/api/analyze`（LLM）   验证 Supabase JWT，保护 LLM key
        └─→ DeepSeek API
```

**部署形态**：
- 前端 → Vercel（静态）
- FastAPI → **Vercel Python Serverless Function**（同域 `/api/*`，无 CORS）

**域名**：阿里云域名 + CNAME → `cname.vercel-dns.com`。**不需要 ICP 备案**（服务器在海外）。

---

## 关键决策：手机号当用户名的实现

Supabase 的手机号登录**必须配 SMS 服务商**（按条计费），免费版不含。

**改用"合成邮箱"方案**：

```js
// 用户界面输入：手机号 + 密码
// 底层调用：email + password
const syntheticEmail = `${phone}@phone.local`

// 注册
await supabase.auth.signUp({
  email: syntheticEmail,
  password,
  options: { data: { nickname, phone } },
})

// 登录
await supabase.auth.signInWithPassword({ email: syntheticEmail, password })
```

**必须在 Supabase 后台关闭**：`Authentication → Providers → Email → Confirm email = OFF`。

这样不发送任何邮件/短信，用户感知就是"手机号+密码"。

> 局限：忘记密码无法自助找回（MVP 可接受，README 里写明）。

---

## 批次 A：数据库 + RLS（半天）

### A.1 表结构

在 Supabase SQL Editor 执行（**顺序不能变**）：

```sql
-- 1. 用户资料（扩展 auth.users）
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nickname text not null,
  phone text,
  created_at timestamptz not null default now()
);

-- 2. 曲库
create table public.tracks (
  id text primary key,
  title text not null,
  artist text not null default '待确认',
  file_url text not null,
  quadrant text not null check (quadrant in ('melancholic','anxious','joyful','calm')),
  license text not null default 'PLACEHOLDER',
  source text,
  created_at timestamptz not null default now()
);

-- 3. 情绪胶囊
create table public.capsules (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  input_text text not null,
  emotions jsonb not null,
  valence double precision not null,
  arousal double precision not null,
  keywords jsonb not null default '[]'::jsonb,
  fine_labels jsonb not null default '[]'::jsonb,
  track_id text references public.tracks(id),
  comment text not null default '',
  created_at timestamptz not null default now()
);

create index capsules_user_created_idx on public.capsules (user_id, created_at desc);
create index capsules_created_idx on public.capsules (created_at desc);
```

### A.2 注册时自动建 profile（触发器）

```sql
create function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, nickname, phone)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'nickname', split_part(new.email, '@', 1)),
    new.raw_user_meta_data->>'phone'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

### A.3 RLS（**这一节配错 = 全网可读用户隐私**）

```sql
alter table public.profiles enable row level security;
alter table public.tracks   enable row level security;
alter table public.capsules enable row level security;

-- profiles：只能读写自己
create policy "profiles_select_own" on public.profiles
  for select using (auth.uid() = id);
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- tracks：所有人可读（曲库是公开数据）
create policy "tracks_select_all" on public.tracks
  for select using (true);

-- capsules：本人全部权限
create policy "capsules_select_own" on public.capsules
  for select using (auth.uid() = user_id);
create policy "capsules_insert_own" on public.capsules
  for insert with check (auth.uid() = user_id);
create policy "capsules_delete_own" on public.capsules
  for delete using (auth.uid() = user_id);

-- capsules：管理员可读全部
-- 前提：管理员账号在 app_metadata 里设置 {"role":"admin"}
create policy "capsules_select_admin" on public.capsules
  for select using (
    coalesce((auth.jwt() -> 'app_metadata' ->> 'role'), '') = 'admin'
  );
```

**管理员设置**（在 Dashboard → Authentication → Users 里给管理员用户编辑 app_metadata）：

```json
{ "role": "admin" }
```

### A.4 种子数据

插入 4 首曲目（沿用现有 id）：

```sql
insert into public.tracks (id, title, artist, file_url, quadrant, license) values
  ('melancholic-1', 'melancholic-1', '待确认', '/audio/melancholic-1.mp3', 'melancholic', 'PLACEHOLDER'),
  ('anxious-1',     'anxious-1',     '待确认', '/audio/anxious-1.mp3',     'anxious',     'PLACEHOLDER'),
  ('joyful-1',      'joyful-1',      '待确认', '/audio/joyful-1.mp3',      'joyful',      'PLACEHOLDER'),
  ('calm-1',        'calm-1',        '待确认', '/audio/calm-1.mp3',        'calm',        'PLACEHOLDER');
```

### A.5 验收（安全测试，必须逐条实测）

- [ ] 用 SQL Editor 的 `anon` 角色上下文，未登录执行 `select * from capsules` → **返回 0 行，不报错**
- [ ] 用户 A 注册后插一条胶囊；用用户 B 的 token 查 → **0 行**
- [ ] 用户 A 能查到自己的 1 行
- [ ] 给管理员设置 `app_metadata.role=admin` 后，能查到所有用户的胶囊
- [ ] 未登录 `select * from tracks` → 返回 4 行（公开可读）
- [ ] 未登录 `insert into capsules` → **被拒绝（RLS 拦截）**
- [ ] 注册新用户后，`profiles` 表自动出现对应行，`nickname` 来自 metadata

**报告里必须贴出每条的实际返回行数，不要写"已配置"。**

---

## 批次 B：前端接 Supabase（1–2 天）

### B.0 先读：三条不可违反的约束

**① 曲库必须是静态的，不准从数据库读**

`tracks` 只有 4 首，是**配置**不是**数据**。前端曲库的**唯一来源**是 `src/data/musicLibrary.js`。

- `tracks` 表保留，**只给管理后台用**
- `src/api/music.js` 里的 `fetchTracks()` 必须**删除**，改回同步读取静态对象
- 不得新增任何"从 Supabase 拉曲库"的逻辑
- 不得在 `musicLibrary.js` 之外再造第二份曲库

> 上一轮就是因为违反这条，本地连不上数据库时抛「曲库中没有可用曲目」，整个流程卡死。

**② 本地连不上 Supabase 是已知环境限制，不是设计缺陷**

| 环境 | 能否连 `*.supabase.co` |
|---|---|
| 本机命令行 / Vite dev proxy | ❌ 不行（ECONNRESET，TLS 阶段被切断） |
| 部署后的 Vercel 服务器 | ✅ 可以 |
| 浏览器（本机） | ❌ 不行 |

**因此本地跑真实 Supabase 功能必然失败，这是预期行为。**

**禁止**为了"让本地能跑"做以下任何事：

- 改架构（例如"先查本地再查远程""双写"）
- 新增缓存层 / 备用数据 / 静默回退
- 把远程地址写死成别的值
- 谎报"已验证登录流程"

遇到连接失败，**只做一件事**：给用户显示「网络异常，请稍后重试」。不要自创降级。

**③ 数据流分工（写死，不要自由发挥）**

```
生成胶囊：
  ① 调后端 /api/analyze（LLM）→ emotions / valence / arousal / keywords / fineLabels / comment
  ② 用 valence+arousal 在【静态曲库】里选曲 —— 纯本地计算，零网络
  ③ 把整条胶囊 insert 到 Supabase capsules 表（需要登录态）
  ④ 渲染结果页

读取历史 / 管理后台：
  只从 Supabase 读；失败显示空状态 + 错误提示
```

### B.1 依赖与环境

```bash
npm i @supabase/supabase-js@latest
```

> **必须最新版**。旧版只认 `eyJhbGci` 开头的 anon JWT，不认 `sb_publishable_` 开头的新 key。

`.env` **已存在**，直接使用，不要改文件名、不要新建别的：

```
VITE_SUPABASE_TARGET_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_xxx
VITE_DATA_MODE=api
```

### B.2 client 必须走 `/sb` 代理

```js
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  `${window.location.origin}/sb`,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: false },
  },
)
```

`vite.config.js` 补上 dev 代理：

```js
server: {
  proxy: {
    '/sb': {
      target: process.env.VITE_SUPABASE_TARGET_URL,
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/sb/, ''),
    },
  },
},
```

**硬性检查**：全项目搜索 `supabase.co`，**只允许出现在 `vite.config.js` 里**（且从 env 读）。任何组件、store、api 文件里出现都算不合格。

### B.3 替换认证层

- `src/stores/auth.js` 重写：
  - 不再把 role/nickname 存 localStorage
  - `supabase.auth.getSession()` 初始化
  - `onAuthStateChange` 监听
  - 暴露 `user`（`user_metadata.nickname`）与 `isAdmin`（`app_metadata.role === 'admin'`）
- `src/api/auth.js` 重写：`register(phone, nickname, password)` / `login(phone, password)` / `logout()`

**手机号规范化**：去掉空格与 `+86`，统一 11 位，校验 `/^1[3-9]\d{9}$/`。
**合成邮箱**：`${phone}@phone.local`。

### B.4 登录页改造

- 用户 tab 拆成**登录 / 注册**两个子模式
- 注册：手机号 + 昵称 + 密码（≥6）+ 确认密码
- 登录：手机号 + 密码
- 英文错误映射成中文：
  - `Invalid login credentials` → 手机号或密码错误
  - `User already registered` → 这个手机号已经注册过了
  - `Password should be at least 6 characters` → 密码至少 6 位
  - 网络错误 → 网络异常，请稍后重试

### B.5 数据层

- 新增 `src/api/capsules.js`：`fetchHistory()` / `saveCapsule()`，全部走 Supabase
- **删除** `src/api/music.js` 的远程读取，改为同步返回静态曲库
- `capsules` 表字段映射注意 `jsonb` 类型（`emotions` / `keywords` / `fine_labels`）

### B.6 验收（分两组，不许混）

**A. 本地可验证**

- [ ] `npm run build` 通过
- [ ] `VITE_DATA_MODE=mock` 时全流程可跑，**零网络依赖**
- [ ] 全项目搜 `supabase.co` → 只出现在 `vite.config.js`
- [ ] 全项目搜 `fetchTracks` → **0 处**
- [ ] 全项目搜 `曲库中没有可用曲目` → **0 处**
- [ ] 未登录访问 `/admin` → 跳转登录页
- [ ] 登录页表单校验（手机号格式、密码长度、两次密码一致）都能触发中文提示

**B. 必须部署后验证（本地做不了，报告里如实写"待部署验证"）**

- [ ] 手机号注册，不发送任何短信/邮件
- [ ] 登录成功，刷新后保持
- [ ] 生成胶囊后 Supabase `capsules` 表出现对应行，`user_id` 正确
- [ ] 用户 A 与用户 B 的数据互不可见
- [ ] 管理员账号能看到全站记录（`app_metadata.role=admin` 生效）

> **报告纪律**：B 组没跑就说没跑。写"已打通 Supabase 登录"但实际没验证，一律打回。

---

## 批次 C：FastAPI 瘦身 + Vercel 部署（1 天）

### C.1 FastAPI 只保留 LLM

**删除**：

- `routers/auth.py`、`routers/capsules.py`、`routers/admin.py`、`routers/music.py`
- `models.py`、`db.py`、`deps.py` 中的 JWT 逻辑
- `services/music/`（选曲改在前端，用 Supabase 的 tracks）
- `requirements.txt` 里的 `sqlalchemy`、`pymysql`、`passlib`、`python-jose`

**保留**：

- `services/analyzer/`（llm.py / mock.py / runtime.py）——**原样保留**
- `services/vad.py`——保留，返回 VAD 给前端

**新增**：

- `POST /api/analyze`：接收 `{text}`，**验证 Supabase JWT**，返回 capsule 的「分析部分」（emotions / valence / arousal / keywords / fineLabels / comment / quadrant）
- `GET /api/health`：返回 `{status, analyzer, version}`

### C.2 验证 Supabase JWT

```python
# 用 SUPABASE_JWT_SECRET 验证（Dashboard → Settings → API → JWT Secret）
# audience 必须校验为 "authenticated"
```

**验收**：

- 不带 token → 401
- 带伪造 token → 401
- 带真实用户 token → 200
- key 全部来自环境变量

### C.3 Vercel 部署

```
vercel.json          # rewrites: /api/* → /api/index.py
api/index.py         # FastAPI 入口（ASGI）
frontend 构建输出     dist/
```

环境变量（Vercel 控制台设置，**不加 VITE_ 前缀**）：

```
SUPABASE_JWT_SECRET
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

### C.4 验收

- [ ] `vercel dev` 本地能跑通前端 + `/api/analyze`
- [ ] 部署后 `https://你的域名/api/health` 返回 200
- [ ] 未登录调用 `/api/analyze` → 401
- [ ] 登录后调用 → 200，返回真实 LLM 结果
- [ ] Vercel 环境变量里没有 `VITE_` 前缀的密钥
- [ ] 前端 bundle 里搜 `sk-` 结果为 0

---

## 全局要求

1. **anon key 可以公开，service_role key 绝对不能进前端**（搜 `service_role` 结果必须为 0）
2. 所有 Supabase 查询错误必须处理，不允许静默失败
3. RLS 相关的每个 policy 在报告里贴出**实际测试结果**
4. 保留 `VITE_DATA_MODE=mock` 的完整演示能力

---

## 完成后报告

1. 三批各自的文件变动
2. **RLS 的 7 条安全测试，逐条给实际返回行数**
3. 注册→登录→生成→查历史的完整链路截图或日志
4. `/api/analyze` 的未授权/授权两种响应
5. 前端 bundle 中 `sk-` 与 `service_role` 的检测结果
6. 有没有偏离本规格的地方
