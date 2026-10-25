# S4 ReactBits 组件移植（Vue 3）

> 给 Codex 的任务单。全部组件来自 reactbits.dev（MIT），**必须移植，不能 `npm i` 装 React 版**。

---

## 0. 先认清这些组件是什么（避免误判工作量）

| 组件 | 技术 | 关键依赖 |
|---|---|---|
| `Lightfall` | WebGL2 着色器 | 可能用 `ogl` |
| `Particles` | WebGL2 点云 | 可能用 `ogl` |
| `Radar` | **原生 WebGL2**，6 个 GLSL 程序 + 5 级泛光 | 无（纯 WebGL） |
| `ElasticSlider` | DOM + 弹性动画 | 无 shader |

**它们不是 CSS 特效。** 每个都包含：GLSL 源码（可原样照抄）+ 一套渲染循环 + 资源清理。

---

## 1. 移植总规则（硬性）

1. **GLSL 字符串原样保留**，一个字符都不要改。改 = 出现无法调试的渲染错误。
2. React 外壳改写规则：
   - `useEffect(..., [])` → `onMounted()` + `onBeforeUnmount()`
   - `useRef` → 模块级/组件级普通变量或 `ref()`
   - `useState`（若有）→ `ref()`
   - props 默认值 → `defineProps({ ... })` 的 `default`
3. 需要 `ogl` 时：`npm i ogl`（框架无关，约 50KB）。**不要装 framer-motion / react / @react-three。**
4. 每个组件顶部注释：
   ```js
   // Ported from reactbits.dev/backgrounds/radar (MIT)
   // 改动：React hooks → Vue 生命周期；其余（GLSL / 渲染逻辑）保持原样
   ```
5. **禁止在组件内 `console.log`**，调试完必须删除。

---

## 2. 硬性要求：WebGL2 降级（不做这个就是白屏）

所有 WebGL 组件必须在创建上下文失败时**立刻降级**，不能留白：

```js
const gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true })
if (!gl) {
  // 方案 A：显示一个 CSS 渐变占位（推荐，成本低）
  // 方案 B：组件直接不渲染，父级背景兜底
  emit('unsupported')   // 或设置一个 ref 标记
  return
}
```

父级必须有兜底背景色（`var(--bg-base)` + 径向渐变），**保证 WebGL 挂掉时页面依然完整可看**。

---

## 3. 页面布局变化

### 3.1 登录页

```
底层：Lightfall（全屏，绝对定位，z-index 0）
     ↓
遮罩：rgba(11,10,20,.55) 一层（z-index 1）—— 保证表单可读
     ↓
内容：品牌 + 表单卡片（z-index 2）
```

- Lightfall 颜色取 `--bg-aurora-1`（紫）
- 不要让它比表单更亮：`opacity: 0.55`
- 移动端 `opacity: 0.35`（省电、省 GPU）

### 3.2 结果页播放器（黑胶，**不要唱臂**）

```
┌─────────────────────────┐
│                         │
│     ╭─────────────╮     │  ← 黑胶盘：CSS repeating-radial-gradient 纹路
│    │   ╭───────╮   │    │
│    │  │Particles│  │    │  ← 中心圆：Particles 组件填充，圆形裁剪
│    │   ╰───────╯   │    │
│     ╰─────────────╯     │
│                         │
│      雨夜的退堂鼓         │
│      Loft · 陪伴         │
│          ▶              │
└─────────────────────────┘
```

- 黑胶盘尺寸：桌面 280px，移动端 200px
- 盘面纹路：`repeating-radial-gradient(circle, rgba(255,255,255,.03) 0 1px, transparent 1px 4px)`
- **Particles 放在旋转容器内部**（随盘转，像唱片纹理），并把它自己的 `speed` 降到 0.3
- 播放：`animation: disc-spin 8s linear infinite`
- 暂停：`animation-duration: 60s`（减速而不是定格，避免"一眼假"）
- `prefers-reduced-motion` 命中：不旋转

### 3.3 情绪 DNA 卡片

**Radar 作为背景层，ECharts 雷达图叠在上面**——因为 Radar 是装饰性扫描效果，不表达 8 维数据，直接替换会丢掉信息。

```
z-index 0：Radar（opacity 0.45，颜色取 palette[0]）
z-index 1：ECharts 八维雷达图（现有组件，opacity 0.85）
```

**如果两者叠在一起看不清**，优先降 Radar 的 `opacity` 到 0.25，**不要删数据层**。

### 3.4 播放进度条

用 `ElasticSlider` 替换 S3-下 里的占位进度条：

- 值范围 `0 ~ audio.duration`
- 拖动时 `audio.currentTime = value`
- 拖动手感：拖动中不跟随 `timeupdate`（否则会打架）
- 音频只有 8 秒时也不特殊处理，正常显示

---

## 4. 交付批次

### Batch A（先做，风险低）
1. `Lightfall` → `src/components/fx/Lightfall.vue`，接进登录页
2. `Particles` → `src/components/fx/Particles.vue`，接进黑胶中心

**本批完成后停下，截图 + 报告。**

### Batch B（A 验收通过后）
3. `Radar` → `src/components/fx/Radar.vue`，接进情绪 DNA 卡片背景
4. `ElasticSlider` → `src/components/player/ElasticSlider.vue`，替换进度条

---

## 5. 参数建议（直接用，不要自己调）

| 组件 | 参数 |
|---|---|
| Lightfall | `color: var(--bg-aurora-1)` 的十六进制值，`speed: 0.6`，`opacity: 0.55` |
| Particles | `quantity: 800`（不要 2000+，移动端会卡），`size: 1.2`，`speed: 0.3`，颜色 `palette[0]` |
| Radar | `color: palette[0]`，`speed: 0.5`，`ringCount: 5`，`spokeCount: 8`，`targets: 0`，`mouseInteraction: false`，`opacity: 0.45` |
| ElasticSlider | 无特殊参数 |

> Radar 的 `spokeCount: 8` —— 和你的情绪维度数一致（8 维），视觉上刚好对应。

---

## 6. 验收（可观察）

**Batch A**
- [ ] 登录页能看到流动的光线背景，表单文字依然清晰可读（截 2 张间隔 1s 的图，光线位置不同）
- [ ] 登录页 `canvas` 数量为 1
- [ ] 黑胶盘在播放时**转动**，暂停时**明显变慢但不完全停**
- [ ] 黑胶中心有粒子在动，且随盘缓慢转动
- [ ] 控制台 0 报错、0 警告
- [ ] 强制禁用 WebGL（F12 → Console 执行 `HTMLCanvasElement.prototype.getContext = () => null` 后刷新）→ **页面不白屏**，有兜底背景
- [ ] 375px 下黑胶 200px，登录卡片不溢出
- [ ] `npm run build` 通过

**Batch B**
- [ ] 情绪 DNA 卡片能看到雷达扫描背景，8 维数据轮廓依然可辨（截图对比）
- [ ] 拖动进度条，音频位置跟着变；松手后不跳回
- [ ] 连续拖动 10 次，控制台 0 报错
- [ ] 页面 `canvas` 总数 ≤ 4（登录 1 / 黑胶 1 / 雷达 1 / ECharts 1）
- [ ] 全部页面切一遍，无 WebGL context lost 警告

---

## 7. 完成后报告

1. 每个组件：源文件路径、行数、是否新增依赖
2. WebGL2 降级是怎么实现的（贴代码）
3. 卸载时清理了什么（贴 `onBeforeUnmount`）
4. 页面 `canvas` 数量（实测值）
5. 禁 WebGL 后的截图
6. 有没有偏离本规格的地方
