# AI 情绪胶囊 · 前端规格书 v1

> 给 Codex 的执行文档。**按批次交付，每批做完停下等我确认**，不要一次性生成全部代码。

---

## 0. 给 Codex 的开工指令（复制这段）

```
读 docs/SPEC-前端-v1.md，这是唯一需求来源。

执行规则：
1. 严格按 §9 的批次 S0 → S4 交付，每批结束停下来，输出「本批改动的文件清单 + 如何本地验证」，等我确认后再进入下一批。
2. 不要自创需求。规格书没写的功能不要加，规格书写的不要改。
3. 遇到歧义或缺失（比如缺音频文件、缺图片资源），停下来问我，不要自己编占位逻辑。
4. 技术栈锁定：Vue 3 + Vite + JavaScript（不用 TypeScript）+ Pinia + Vue Router + ECharts + html2canvas。不要引入其他 UI 框架、动画库、粒子库（尤其不要 three.js）。
5. 所有网络请求走 src/api/ 下的封装，第一版全部走 mock，不允许在组件里直接 fetch。
6. 每个 vue 文件顶部用 3 行以内注释说明：这个组件负责什么、它的输入输出是什么。
```

---

## 1. 项目目标与边界

**一句话**：用户描述心情 → AI 解析 → 播放匹配的音乐 + 可视化情绪图谱 → 导出分享卡片。

### 第一版做（In Scope）

- 登录页：用户（昵称直接进）/ 管理员（账号密码）
- 三个状态的完整流转：情绪输入 → 解析动画 → 情绪胶囊结果页
- 音乐播放器（含 Canvas 音频可视化）
- 情绪雷达图（ECharts）+ 关键词词云
- AI 疗愈语展示
- 保存为图片（html2canvas）
- 管理后台：情绪记录列表 + 简单统计

### 第一版不做（Out of Scope，防止 Codex 过度发挥）

- ❌ 真实后端、真实数据库
- ❌ 真实 AI 调用（用 mock 返回固定样本）
- ❌ 注册、找回密码、第三方登录
- ❌ 音频版权处理（用本地占位文件）
- ❌ 移动端深度适配（响应式做到"不塌"，不做精细断点）
- ❌ 国际化（只做中文）

---

## 2. 技术栈与选型理由

| 技术 | 用途 | 为什么是它 |
|---|---|---|
| Vue 3（Composition API） | 框架 | 与课程技术栈一致，学习成本最低 |
| Vite | 构建 | 快，配置少 |
| **JavaScript（不用 TS）** | 语言 | 降低理解成本；投递需要 TS 的岗位时再补 |
| Pinia | 状态管理 | 存情绪结果、登录态 |
| Vue Router | 路由 | 三个页面 + 路由守卫 |
| ECharts | 雷达图 | 规格书要求，且占位清晰 |
| echarts-wordcloud | 词云 | ECharts 官方扩展 |
| html2canvas | 导出图片 | 规格书要求（有坑，见 §10） |
| Element Plus | **仅管理后台**的表格与表单 | 不用于 C 端页面，避免和自定义视觉冲突 |

**不引入**：three.js、GSAP、Animate.css、Tailwind。C 端视觉全部手写 CSS，方便你理解和调。

---

## 3. 目录结构（照此创建，不要改名）

```
src/
├── main.js
├── App.vue
├── router/
│   └── index.js
├── stores/
│   ├── auth.js              # 登录态：{ role: 'user'|'admin'|null, nickname }
│   └── emotion.js           # 当前情绪结果 + 状态机 stage
├── api/
│   ├── mock.js              # mock 数据源（含 3 组以上样本）
│   ├── emotion.js           # analyzeMood(text) -> Promise<Capsule>
│   └── auth.js              # login(nickname) / adminLogin(username,password)
├── views/
│   ├── LoginView.vue
│   ├── CapsuleView.vue      # 核心页，管状态机
│   └── AdminView.vue
├── components/
│   ├── AuroraBackground.vue # 极光 + 粒子背景（canvas）
│   ├── stages/
│   │   ├── MoodInputStage.vue    # 状态一
│   │   ├── AnalyzingStage.vue    # 状态二
│   │   └── ResultStage.vue       # 状态三（容器）
│   ├── player/
│   │   ├── MusicPlayer.vue       # 播放器 + 音频可视化
│   │   └── AudioVisualizer.vue   # canvas 波形/呼吸环
│   ├── EmotionRadar.vue
│   ├── KeywordCloud.vue
│   ├── HealingComment.vue
│   └── ShareCard.vue             # 导出按钮 + 逻辑
├── composables/
│   └── useEmotionFlow.js    # 状态机逻辑（S1→S2→S3）
├── assets/
│   └── styles/
│       └── tokens.css       # 设计变量（颜色/玻璃拟态/动效时长）
public/
├── audio/                   # 占位音频（见 §8）
└── covers/                  # 占位封面
```

---

## 4. 路由与权限

| 路径 | 组件 | 守卫 |
|---|---|---|
| `/login` | LoginView | 已登录则跳 `/` |
| `/` | CapsuleView | 未登录跳 `/login` |
| `/admin` | AdminView | 非 admin 跳 `/login` |

**认证规则（第一版）**

- 用户登录：输入昵称（≥2 字）即可，无需密码。`auth.login(nickname)`
- 管理员登录：固定账号 `admin` / 密码 `admin123`（写在 `api/auth.js` 里，加注释 `TODO: 接入后端后删除`）
- 登录态存 `localStorage`，key = `capsule_auth`
- 刷新页面保持登录态

---

## 5. 状态机（这是整个项目的骨架）

| 状态 | stage 值 | 触发 | 界面 | 退出条件 |
|---|---|---|---|---|
| 输入 | `input` | 进入 `/` 或点"再来一个" | 居中发光标题 + 玻璃输入框 + 生成按钮 | 文本长度 ≥ 4 且点击生成 |
| 输入-校验失败 | `input` | 文本 < 4 字 | 输入框左右抖动 0.3s + 提示"再多说一点" | 自动回到输入 |
| 解析中 | `analyzing` | 提交成功 | 全屏遮罩 + 粒子加速 + 三条文案依次浮现 | mock 返回（延迟 1.8–3.2s 随机） |
| 解析失败 | `error` | mock 抛错 | 回到输入态 + 顶部 toast"解析失败，请重试" | 用户重新提交 |
| 结果 | `result` | 解析成功 | 左播放器 / 右图谱 + 分享按钮 | 点"再来一个"回输入 |

**三条解析文案（按顺序，每条停留 600ms，淡入淡出）**

1. `正在提取关键词：[{{ 关键词 }}]...`
2. `情感向量计算中...`
3. `正在为你寻找专属旋律...`

第一条里的关键词取自 mock 返回的 `keywords` 前 3 个。

---

## 6. 数据契约（Codex 必须严格遵守字段名）

```js
// 情绪结果胶囊
{
  capsuleId: "cap_20261024_001",
  createdAt: "2026-10-24T22:30:00+08:00",
  input: "今天面试被挂了，外面还在下雨，感觉好累",

  // 八维情绪，0-100 的整数，用于雷达图；顺序与 EMOTION_DIMENSIONS 一致
  emotions: {
    "喜悦": 3,
    "期待": 18,
    "平静": 20,
    "温暖": 10,
    "悲伤": 78,
    "焦虑": 62,
    "疲惫": 80,
    "孤独": 55
  },

  // 由 emotions 计算得出，禁止在样本中手写
  valence: -1,
  arousal: 0,

  // 3-5 个从原文提取的实词，用于解析文案与结果页“关于…”小字
  keywords: ["面试", "下雨", "退堂鼓", "潮湿", "撑住"],

  // 5-8 个情绪形容词/状态词，用于词云
  fineLabels: ["挫败", "无力", "被否定", "潮湿", "撑不住"],

  music: {
    id: "m_001",
    title: "雨夜的退堂鼓",
    artist: "Lo-fi Room",
    cover: "/covers/rain-night.jpg",
    audioUrl: "/audio/rain-night.mp3",
    bpm: 72,
    tags: ["Lo-fi", "雨声", "钢琴"]
  },

  // AI 疗愈语，2-3 句
  comment: "别灰心，这场雨总会停的。听听这首 Lo-fi，就当是我陪着你。",

  // 主题色，用于结果页极光渐变（两个十六进制色）
  palette: ["#7C5CFF", "#FF8FB1"]
}
```

**设计约束（重要）**

- `emotions` 的 8 个键**固定不变**，顺序固定：喜悦、期待、平静、温暖、悲伤、焦虑、疲惫、孤独。雷达图按这个顺序画。
- `valence` / `arousal` 必须由 `computeVAD(emotions)` 计算，禁止在样本中手写。
- `keywords` 是从原文提取的实词，`fineLabels` 是情绪形容词/状态词；两者用途不同，不要合并。
- `palette` 决定结果页背景色调，取值要跟 `emotions` 的主导情绪匹配（悲伤偏蓝紫、喜悦偏暖橙）。

---

## 7. Mock 数据要求

`src/api/mock.js` 至少准备 **4 组样本**，覆盖不同情绪基调：

| 样本 | 输入 | 主导情绪 | 配色 |
|---|---|---|---|
| 1 | 今天面试被挂了，外面还在下雨，感觉好累 | 疲惫 + 悲伤 | 蓝紫 |
| 2 | 我终于拿到 offer 了，想大喊一声 | 喜悦 + 期待 | 暖橙 |
| 3 | 一个人在外地，晚上有点想家 | 孤独 + 平静 | 深蓝 |
| 4 | 明天要答辩，紧张到睡不着 | 焦虑 + 疲惫 | 青灰 |

**选择逻辑**：`analyzeMood(text)` 里用最简单的关键词匹配（包含"累/雨/挂"→样本1，含"offer/拿到"→样本2…），匹配不到默认样本 1。**不要**写复杂算法，第一版只要能演示不同结果即可。

---

## 8. 视觉规范（写进 tokens.css）

```css
:root {
  /* 背景 */
  --bg-base: #0B0A14;
  --bg-aurora-1: #7C5CFF;   /* 会被结果页 palette 覆盖 */
  --bg-aurora-2: #FF8FB1;

  /* 玻璃拟态 */
  --glass-bg: rgba(255, 255, 255, 0.06);
  --glass-border: rgba(255, 255, 255, 0.12);
  --glass-blur: 16px;

  /* 文字 */
  --text-primary: rgba(255, 255, 255, 0.95);
  --text-secondary: rgba(255, 255, 255, 0.55);

  /* 动效时长 */
  --dur-fast: 200ms;
  --dur-base: 400ms;
  --dur-slow: 800ms;
  --ease-soft: cubic-bezier(0.4, 0, 0.2, 1);
}
```

**字体**：`system-ui, "PingFang SC", "Microsoft YaHei", sans-serif`。标题加 `letter-spacing: 0.08em` + `text-shadow` 发光。**不要引入网络字体**（加载慢且中文包巨大）。

**标题发光**（状态一）：

```css
.title {
  font-size: clamp(24px, 4vw, 40px);
  font-weight: 300;
  letter-spacing: 0.1em;
  color: var(--text-primary);
  text-shadow: 0 0 24px rgba(124, 92, 255, 0.6),
               0 0 60px rgba(124, 92, 255, 0.3);
}
```

**背景实现**：`AuroraBackground.vue` 用**一个 canvas** 绘制：

- 底层：两团径向渐变的模糊光斑，用 `filter: blur(80px)` 的 div 做也行（更省性能）
- 粒子：`ctx.fillRect` 画 60–100 个缓慢漂移的小点，`requestAnimationFrame` 驱动
- 解析态时粒子速度 ×2.5，结果态恢复正常
- **必须**支持 `prefers-reduced-motion`：命中时粒子静止

---

## 9. 交付批次（Codex 严格按此顺序，每批停下）

### S0 工程初始化（预计 10 分钟）
- Vite 创建 Vue 项目，装依赖：`pinia vue-router echarts echarts-wordcloud html2canvas element-plus`
- 建目录结构、`tokens.css`、全局样式重置
- 产出：`npm run dev` 能起，页面白屏但无报错

**验收**：`npm run dev` 无报错，首页显示一行"项目已就绪"。

### S1 登录 + 路由骨架（预计 30 分钟）
- `LoginView`：两个 tab（我是用户 / 我是管理员）
  - 用户 tab：昵称输入框 + "进入"按钮
  - 管理员 tab：用户名 + 密码 + "登录"按钮
- `auth` store + `api/auth.js`（mock）
- 路由守卫、`CapsuleView` 和 `AdminView` 空壳

**验收**：昵称登录 → 跳 `/`；`admin`/`admin123` → 跳 `/admin`；错误密码有提示；刷新保持登录。

### S2 状态一 + 状态二（预计 60 分钟）
- `AuroraBackground`
- `MoodInputStage`：发光标题、玻璃输入框、生成按钮、Loading 态、抖动校验
- `AnalyzingStage`：全屏遮罩 + 三条文案轮播
- `useEmotionFlow` 状态机 + `api/emotion.js` mock

**验收**：输入 8 个字点生成 → 看到三条文案依次出现 → 1.8–3.2s 后到结果态（此时结果页可先放占位文字）。

### S3 状态三：播放器 + 雷达图 + 词云（预计 90 分钟）
- `MusicPlayer` + `AudioVisualizer`（AnalyserNode 真实频谱，无音频时降级为呼吸环）
- `EmotionRadar`（ECharts，6 维，主色高亮）
- `KeywordCloud`（echarts-wordcloud）
- `HealingComment`
- 布局：桌面端左右分栏（`grid-template-columns: 1fr 1fr`），窄屏上下堆叠

**验收**：音频能播放/暂停；波形随音乐跳动；雷达图 6 个轴标签正确；词云显示关键词；配色跟随 `palette`。

### S4 分享导出 + 管理后台（预计 60 分钟）
- `ShareCard`：html2canvas 导出 PNG，文件名 `情绪胶囊-{日期}.png`
- `AdminView`：情绪记录列表（`el-table`）+ 2 个统计图（情绪分布柱状图、每日生成量折线图）

**验收**：点导出 → 下载一张图，图中包含封面、标题、雷达图、寄语；后台能看到 mock 记录列表。

---

## 10. 已知的坑（Codex 必须避开）

### 坑 1：html2canvas 渲染不了 `backdrop-filter`

玻璃拟态靠 `backdrop-filter: blur()`，而 html2canvas **不支持它**，导出图会是半透明甚至黑色块。

**解法**：导出前给根容器加 `.exporting` 类，把玻璃元素换成不透明背景色，导出完移除：

```js
// ShareCard.vue
async function exportCard() {
  const el = document.getElementById('capsule-card')
  document.body.classList.add('exporting')
  await nextTick()
  const canvas = await html2canvas(el, { backgroundColor: '#0B0A14', scale: 2, useCORS: true })
  document.body.classList.remove('exporting')
  // 下载
}
```

```css
.exporting .glass { backdrop-filter: none; background: rgba(30, 28, 50, 0.92); }
```

### 坑 2：Canvas 和 ECharts 图表在导出时可能是空白

ECharts 渲染在 canvas 里，html2canvas 有时抓不到。导出前调用：

```js
// 确保图表已渲染完
await nextTick()
await new Promise(r => setTimeout(r, 150))
```

若仍空白，改用 `echartsInstance.getDataURL()` 拿图片，替换 canvas 后再导出。

### 坑 3：音频自动播放被浏览器拦截

用户没交互前 `audio.play()` 会报 `NotAllowedError`。**必须**等用户点击"播放"按钮后再播；不要一进结果页就自动 play。

### 坑 4：音频文件缺失

`public/audio/` 下先放 **3 个短的免版权 mp3**（或用 1 个文件复制改名）。如果拿不到，就让 `<audio>` 的 `src` 指向空字符串并显示"音频占位"，**不要**写死外链（会因跨域/CORS 失败）。

### 坑 5：ECharts 在响应式容器里尺寸计算错误

图表初始化时容器宽高可能为 0。**必须**用 `ResizeObserver` 监听容器，或 `setTimeout(() => chart.resize(), 0)`。

---

## 11. 工程规范

- 组件名 PascalCase，文件名与组件名一致
- 样式默认 `scoped`，全局变量只放 `tokens.css`
- 不允许 `console.log` 留在提交里（调试完删掉）
- 所有 mock 延迟用 `await sleep(random(1800, 3200))`，不要写死一个值
- 每个 `.vue` 文件不超过 250 行；超了就拆组件

---

## 12. 验收清单（全部前端，S4 结束后自检）

- [ ] `npm run dev` 无报错、无警告
- [ ] 昵称登录 → 首页 → 生成 → 结果 全流程通
- [ ] 输入不足 4 字有提示，不会请求
- [ ] 解析态文案依次出现，不重叠
- [ ] 结果页配色随情绪变化（4 组样本颜色不同）
- [ ] 音频可播可停，波形随节奏动
- [ ] 雷达图 6 轴正确、数值与 mock 一致
- [ ] 词云显示 3-6 个关键词
- [ ] 导出图片清晰，无黑块、无空白图表
- [ ] `admin/admin123` 能进后台，错误密码进不去
- [ ] 刷新页面登录态保持
- [ ] 窄屏（375px）布局不塌
