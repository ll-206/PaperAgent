# PaperAgent 登录页 · 方案 B 增补提示词 ③（Neumorphism 新拟物 × 品牌紫）

> 用途：在**已完成的方案 B（分栏 + 圆润苹果风 + 玻璃感）**基础上，把整体质感改造成 **Neumorphism（新拟物派 / Soft UI）**——柔和的内凹外凸立体、双光源阴影、浅色同色系背景。
> **硬约束：主色调不变（品牌紫 `#6d5bd0`）、功能不变、文字不变、Logo 不变、左右分栏与响应式不变。颜色可整体微调深浅。**
> 目标文件：仍只改 `PaperQuery_Frontend/src/views/login/login.vue`。

---

## 一、从 Neumorphism 学到的核心规则（本提示词的依据）

| 规则 | 含义 | 在登录页的落地 |
|---|---|---|
| **双光源阴影** | 亮阴影在左上（-X/-Y，`#ffffff`），暗阴影在右下（+X/+Y，`#b8bcc2`） | 所有卡片/按钮/卖点卡都用这套双阴影 |
| **凸起 vs 凹陷** | 凸起=可交互，凹陷=输入区/按下 | 卡片、按钮凸起；输入框凹陷；按钮按下变凹陷 |
| **浅色同色系背景** | 背景 `#e0e5ec` / `#f0f0f3`，元素同色系 | 页面改浅灰底；品牌紫降为强调色 |
| **无边框、无渐变** | 靠阴影分隔，不用 border/gradient | 去掉实边框与紫渐变，改用阴影 |
| **柔和圆角** | `rounded-xl`（12px）/`rounded-2xl`（16–24px） | 卡片 24px、输入框/按钮 14px |
| **状态反馈** | hover 阴影缩小、active 凹陷、focus 内阴影变浅 | 照做 |

---

## 二、功能与内容红线（绝对不变）

- **不改** `script` 逻辑、登录校验、接口、路由、字段文案（用户名/密码/登录/本地体验账号 admin / 123456/英文标语）。
- **Logo 沿用** `@/assets/img/paperagent-mark.png`，不替换、不重绘。
- **不改**左右分栏与响应式（≥1024px 分栏，<1024px 只显右侧表单）。
- **主色不变**：强调色固定 `#6d5bd0`（可微调深浅，如 hover 用 `#5e4bc2`），**不要**换成新拟物默认的 `#6d5dfc`。
- 只允许调整**样式**，以及承载新拟物质感的**纯装饰容器**（不新增图片文件）。

---

## 三、颜色 / 阴影 / 圆角 Token（本项目专用映射）

| Token | 值 | 用途 |
|---|---|---|
| 页面背景 | `#e0e5ec`（右区）/ 左侧用品牌紫浅变体 `#e9e6f9` | 浅色同色系底 |
| 暗阴影 | `#b8bcc2` | 右下 +X/+Y |
| 亮阴影 | `#ffffff` | 左上 -X/-Y |
| 强调色（主色不变） | `#6d5bd0`，hover `#5e4bc2` | 按钮、图标、标题、Logo 容器 |
| 主文字 | `#333333` | 标题、正文 |
| 次要文字 | `#6b7280` | 描述、标签 |
| 圆角 | 卡片 `24px`、输入框/按钮 `14px`、卖点卡 `16px` | 柔和一致 |
| 过渡 | `transition: all 0.3s ease-in-out` | 软塑料柔韧感 |

---

## 四、具体 CSS（写入 `<style scoped>`）

### 1. 页面与左侧品牌区（浅色同色系，品牌紫作强调，去掉渐变）

```css
.login-page {
  background: #e0e5ec;              /* 新拟物浅灰主底 */
}

/* 左侧品牌区：不再用深紫渐变，改品牌紫浅色变体（同色系浅色） */
.brand-panel {
  background: #e9e6f9;              /* 品牌紫浅变体，浅色、同色系 */
  position: relative;
  overflow: hidden;
}

/* 左侧品牌区：加极淡的网格线装饰（可保留之前的科研感，保持低透明度） */
.brand-panel::after {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0.06;
  background-image:
    linear-gradient(rgba(109, 91, 208, 0.5) 1px, transparent 1px),
    linear-gradient(90deg, rgba(109, 91, 208, 0.5) 1px, transparent 1px);
  background-size: 44px 44px;
  pointer-events: none;
}
```

> 左侧大标题、副标、英文标语改为品牌紫/深灰，图标与卖点卡用品牌紫（见下）。若想要更强品牌冲击力，可把左区背景换成品牌紫**更深**变体（如 `#5b4ac4`）并把文字改白——但为贴合新拟物"浅色背景"，推荐默认用浅紫变体。

### 2. 登录卡片：凸起（默认）

```css
.login-card {
  background: #f0f0f3;              /* 抬升表面，同色系略浅 */
  border: none;                      /* 新拟物无边框 */
  border-radius: 24px;
  box-shadow:
    8px 8px 16px #b8bcc2,          /* 暗：右下 */
    -8px -8px 16px #ffffff;        /* 亮：左上 */
}
```

### 3. 输入框：凹陷（默认），focus 变浅（通道开放）

```css
.login-card input {
  background: #e0e5ec;
  border: none;
  border-radius: 14px;
  height: 48px;
  padding: 0 16px;
  box-shadow:
    inset 6px 6px 12px #b8bcc2,          /* 默认：深凹陷 */
    inset -6px -6px 12px #ffffff;
  transition: box-shadow 0.3s ease-in-out;
}
.login-card input:focus {
  outline: none;
  box-shadow:
    inset 2px 2px 4px #b8bcc2,           /* focus：内阴影变浅 */
    inset -2px -2px 4px #ffffff,
    0 0 0 3px rgba(109, 91, 208, 0.20);  /* 可选：品牌紫轻 ring，可去掉 */
}
```

### 4. 登录按钮：凸起 → hover 缩小 → active 凹陷（品牌紫 CTA）

```css
.login-button {
  background: #6d5bd0;              /* 主色不变，作 CTA */
  color: #fff;
  border: none;
  border-radius: 14px;
  height: 48px;
  box-shadow:
    8px 8px 16px #b8bcc2,
    -8px -8px 16px #ffffff;
  transition: all 0.3s ease-in-out;
}
.login-button:hover {
  box-shadow:
    4px 4px 8px #b8bcc2,           /* hover：阴影缩小（手指靠近遮光） */
    -4px -4px 8px #ffffff;
  background: #5e4bc2;             /* 主色变深 */
}
.login-button:active {
  box-shadow:
    inset 4px 4px 8px #b8bcc2,     /* active：凸起转凹陷，禁止 translate */
    inset -4px -4px 8px #ffffff;
}
```

### 5. 左侧卖点卡：小凸起 + 品牌紫图标（白/浅紫圆形容器）

```css
.selling-point-card {
  background: #f0f0f3;
  border: none;
  border-radius: 16px;
  box-shadow:
    4px 4px 8px #b8bcc2,
    -4px -4px 8px #ffffff;
}
.selling-point-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e9e6f9;             /* 品牌紫浅变体圆底 */
  color: #6d5bd0;                  /* 图标品牌紫 */
  box-shadow:
    inset 2px 2px 4px rgba(0, 0, 0, 0.08),
    inset -2px -2px 4px rgba(255, 255, 255, 0.8);  /* 内凹感，或去掉改凸起 */
}
```

### 6. 顶部 Logo：放入凸起圆形容器（沿用 logo 图片）

```css
.brand-logo-container {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #f0f0f3;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow:
    4px 4px 8px #b8bcc2,
    -4px -4px 8px #ffffff;
}
/* 图片本身仍是 <img :src="paperAgentMark">，不替换文件 */
```

---

## 五、冲突处理说明（重要，务必照做）

1. **去掉方案 B 左侧的紫渐变**（`linear-gradient(#6d5bd0,#4a3f9a)`）——新拟物禁止渐变。改用品牌紫浅色变体 `#e9e6f9` 纯色。
2. **去掉所有 `border: 1px solid ...` 实边框**——新拟物靠阴影分隔，不用边框。
3. **去掉之前的 `backdrop-filter` 毛玻璃**（玻璃感与本风格冲突）——改用双阴影立体。
4. **按钮禁止 `transform: translateY(-1px)`**（新拟物元素长在背景上，不浮起）；active 用 inset 阴影而非位移。
5. **主色只允许微调深浅**（`#6d5bd0`↔`#5e4bc2`，及浅变体 `#e9e6f9`），不得换色相。
6. 图标继续用 `lucide-vue-next`（`Search` / `FileText` / `Layers`），不新增图片。

---

## 六、验收清单（交付前自查）

1. 功能、文字、Logo、分栏与响应式零改动（git diff 复核）。
2. 背景为浅灰 `#e0e5ec`（右区）+ 品牌紫浅变体 `#e9e6f9`（左区），无纯黑/纯白背景、无渐变。
3. 所有立体元素均为**双光源阴影**：亮在左上（`#ffffff`）、暗在右下（`#b8bcc2`）。
4. 登录卡片凸起；输入框凹陷、focus 内阴影变浅；按钮 hover 阴影缩小、active 转凹陷且无 translate。
5. 无 `border`、无 `backdrop-filter`、无 `translate`、无 `bg-gradient-*`。
6. 品牌紫 `#6d5bd0` 作为强调色贯穿（按钮/图标/标题/Logo），整体一眼可辨为 Neumorphism。
7. 过渡统一 `0.3s ease-in-out`；`vue-tsc` / `vite` 构建通过，无控制台报错。
