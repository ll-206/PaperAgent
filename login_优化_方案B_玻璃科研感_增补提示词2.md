# PaperAgent 登录页 · 方案 B 增补提示词 ②（玻璃感 + 高级科研感）

> 用途：在**已完成的方案 B（含圆润苹果风）**基础上再精修一次，强化「玻璃拟态」质感并注入「高级科研」氛围。不改功能、不改布局结构。
> 目标文件：仍只改 `PaperQuery_Frontend/src/views/login/login.vue`。
> 场景：上一版已做到分栏 + 大圆角 + 白底图标。用户进一步要求**玻璃感**与**高级科研感**——希望整体像一块精致的磨砂玻璃研究面板，冷峻、克制、专业。

---

## 一、功能红线（重申，与之前完全一致）

- **不改** `script` 逻辑、登录校验、接口、路由、字段文案、Logo（`paperagent-mark.png` 沿用）。
- **不改**左右分栏结构与响应式规则（≥1024px 分栏，<1024px 只显右侧表单）。
- **不改**卖点内容（证据可溯源 / 混合检索问答 / 科研任务编排），图标保持白底圆形。
- 你只允许调整**样式**与新增**纯展示**的装饰元素（CSS/SVG 伪元素，不新增图片文件）。

---

## 二、改动点 1：强化「玻璃感」（Glassmorphism）

玻璃感的三个要素：**半透明底色 + 背景模糊 + 高光细边**。逐项落地：

### 1. 右侧表单区改为淡紫渐变底 + 光晕（与左侧呼应）

```css
.login-shell {
  background: linear-gradient(135deg, #f7f6fb 0%, #efedf8 55%, #e9e6f5 100%);
  position: relative;
}
.login-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 78% 20%, rgba(109, 91, 208, 0.10), transparent 42%),
    radial-gradient(circle at 15% 80%, rgba(139, 126, 230, 0.08), transparent 45%);
  pointer-events: none;
}
```

### 2. 登录卡片玻璃化（半透明白 + 模糊 + 顶部高光）

```css
.login-card {
  background: rgba(255, 255, 255, 0.68);        /* 半透明白 */
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  backdrop-filter: blur(20px) saturate(180%);    /* 背后光晕被模糊，形成磨砂玻璃 */
  border: 1px solid rgba(255, 255, 255, 0.6);   /* 半透明白描边 */
  border-radius: 24px;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.85),    /* 顶部高光线：玻璃反光 */
    0 2px 4px rgba(0, 0, 0, 0.05),
    0 18px 48px rgba(93, 79, 168, 0.12);
}
```

> 若卡片半透明后文字可读性下降，把 `rgba(255,255,255,0.68)` 提到 `0.75~0.8`，并保持模糊，兼顾质感与可读。

### 3. 左侧卖点卡强化玻璃细节（更明显的磨砂 + 高光）

```css
.selling-point-card {
  background: rgba(255, 255, 255, 0.14);
  -webkit-backdrop-filter: blur(16px) saturate(170%);
  backdrop-filter: blur(16px) saturate(170%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35);   /* 顶部玻璃高光 */
    0 4px 16px rgba(0, 0, 0, 0.10);
  border-radius: 16px;
}
```

### 4. 输入框微玻璃化（iOS 浅灰内嵌 + 极淡投影）

```css
.login-card input {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04);
}
.login-card input:focus {
  box-shadow: 0 0 0 3px rgba(109, 91, 208, 0.25);
}
```

---

## 三、改动点 2：注入「高级科研感」

科研感 = **冷调配色 + 克制的留白 + 细线数据图形装饰 + 精致字体**，不做成花哨科技感，而是冷峻、专业、有"研究平台"气质。

### 1. 左侧渐变偏冷、更深邃（紫→靛→深蓝紫）

```css
.brand-panel {
  background: linear-gradient(165deg, #6d5bd0 0%, #4f3fc0 38%, #3d3690 72%, #2f2a72 100%);
}
```

### 2. 背景加「科研图形」细线装饰（低透明度，营造数据/论文感）

在左侧品牌区叠加极细的坐标网格线与数据点，模拟科研图谱：

```css
.brand-panel::after {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0.08;                               /* 极淡，不抢主体 */
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.6) 1px, transparent 1px),  /* 横细线 */
    linear-gradient(90deg, rgba(255, 255, 255, 0.6) 1px, transparent 1px); /* 竖细线 */
  background-size: 44px 44px;
  -webkit-mask-image: radial-gradient(circle at 50% 40%, #000 0%, transparent 78%);
          mask-image: radial-gradient(circle at 50% 40%, #000 0%, transparent 78%);
  pointer-events: none;
}
```

（如项目对性能/样式更友好，可用一个内联 SVG 的细网格/点阵装饰替代，仍不新增图片文件。）

### 3. 卖点图标更精致（科研图标语义 + 白底微调）

- 图标语义可贴合科研：如 `Search`（检索）、`FileText`（文献/论文）、`Layers` 或 `Braces`（结构化/编排）。沿用 `lucide-vue-next`，不新增图片。
- 白底圆形容器可改为**极浅紫圆角方形** `background:rgba(255,255,255,0.95)`，图标 `#6d5bd0`，加一条 `inset` 高光，更贴合玻璃面板。

### 4. 字体与排版更克制、专业

```css
.login-page {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
    "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}
/* 主标题：更轻盈字重、适度字距，显得高级 */
.brand-panel h2 {
  font-weight: 500;          /* 勿用 700 过粗 */
  letter-spacing: 0.01em;
}
/* 副标/描述：更浅更灰，拉开层次 */
.brand-panel .subtitle,
.card-description {
  color: rgba(255, 255, 255, 0.72);
}
```

### 5. 统一柔和过渡（保持苹果风顺滑）

- 给卡片、按钮、输入框、卖点卡加 `transition: all 0.2s ease;`。
- 卡片 hover 可轻微上浮 + 阴影加深，增强"可触"的玻璃面板质感。

---

## 四、验收清单

1. 功能零改动（`script`、接口、路由、文案、Logo 均未变，git diff 复核）。
2. 登录卡片与卖点卡有明显的**磨砂玻璃感**：半透明 + `backdrop-filter` 模糊 + 顶部高光线。
3. 右侧表单区为淡紫渐变底 + 光晕，与左侧呼应。
4. 左侧偏冷深邃渐变，带极淡的科研网格/点阵装饰。
5. 卖点图标白底清晰、品牌紫，语义贴合科研。
6. 字体轻盈克制，层次分明，整体呈现"高级科研工作台"气质。
7. 响应式规则未变；`vue-tsc` / `vite` 构建通过，无控制台报错。
