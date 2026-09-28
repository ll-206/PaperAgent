# PaperAgent 登录页 · 方案 B 增补提示词（圆润苹果 iOS 风格 + 图标白底衬托）

> 用途：在**已完成的方案 B 分栏效果**基础上做一次视觉精修，不改任何功能、不改布局结构。
> 目标文件：仍只改 `PaperQuery_Frontend/src/views/login/login.vue`。
> 场景：上一版已实现「左紫渐变品牌区 + 右白底表单」，但用户反馈**太僵硬**，且左侧卖点图标在深紫背景上**看不清**。本次目标是让整体更圆润、柔和、有 iOS 质感，并给图标加白底提高辨识度。

---

## 一、功能红线（与上一版完全一致，重申）

- **不改** `script` 逻辑（`username`/`password`/`url`、`login()`、`ElNotification`、`router.push('/home')`）。
- **不改**登录校验、接口、路由、字段文案（用户名/密码/登录/本地体验账号 admin / 123456/英文标语）。
- **Logo 继续沿用** `@/assets/img/paperagent-mark.png`，不替换、不重绘。
- **不改**左右分栏结构与响应式规则（≥1024px 分栏，<1024px 只显右侧表单）。
- 你只允许微调 **样式**（`<style scoped>`）与新增**纯展示**的图标容器。

---

## 二、改动点 1：整体更圆润、更柔和，走「苹果 iPhone / iOS」质感

iOS 风格的核心：**大圆角、多层柔和阴影、毛玻璃、平滑过渡、轻盈字体、柔和渐变**。逐项落地：

### 1. 圆角全面加大（关键）

| 元素 | 现在 | 改为（iOS 风格） |
|---|---|---|
| 登录卡片 `.login-card` | 16px | **24px** |
| 输入框 | 9px | **14px** |
| 登录按钮 | 9px | **14px** |
| 左侧卖点卡 | 12px | **16px** |
| 图标容器 | 方形 | **圆形 50%**（或 12px 圆角） |

### 2. 阴影更柔和、多层（替代生硬阴影/边框）

```css
/* 登录卡片：去生硬实边框，改 iOS 式柔和多层阴影 */
.login-card {
  border: none;                          /* 去掉原来 1px 硬边框 */
  border-radius: 24px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 12px 32px rgba(93, 79, 168, 0.10); /* 上层柔和、下层扩散 */
}

/* 登录按钮：柔和渐变 + 轻投影，不再平铺一色 */
.login-button {
  height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #7a6cf0, #6d5bd0);
  box-shadow: 0 6px 16px rgba(109, 91, 208, 0.35);
  transition: all 0.2s ease;
}
.login-button:hover {
  box-shadow: 0 8px 20px rgba(109, 91, 208, 0.45);
  transform: translateY(-1px);          /* 轻浮起，iOS 式反馈 */
}
```

### 3. 输入框改 iOS 式「浅灰内嵌底、无边框」

```css
.el-input__wrapper, /* 视项目实际的输入框根节点而定 */
.login-card input {
  height: 48px;
  padding: 0 16px;
  border: none;
  border-radius: 14px;
  background: #f5f5f7;                 /* iOS 浅灰内嵌底 */
  transition: box-shadow 0.2s ease, background 0.2s ease;
}
.login-card input:focus {
  background: #fff;
  box-shadow: 0 0 0 3px rgba(109, 91, 208, 0.25); /* 聚焦紫描边 ring */
}
```

### 4. 左侧品牌区渐变更柔和 + 加光晕

```css
.brand-panel {
  background: linear-gradient(160deg, #6d5bd0 0%, #5b4ac4 45%, #4a3f9a 100%);
  position: relative;
  overflow: hidden;
}
/* 柔和光晕，削弱生硬感 */
.brand-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.10), transparent 42%),
    radial-gradient(circle at 85% 75%, rgba(139, 126, 230, 0.35), transparent 50%);
  pointer-events: none;
}
```

### 5. 卖点卡加毛玻璃质感（iOS 玻璃）

```css
.selling-point-card {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(12px) saturate(160%); /* 玻璃模糊+增饱和 */
  -webkit-backdrop-filter: blur(12px) saturate(160%);
}
```

### 6. 字体更轻盈、系统化（iOS 系统字体）

```css
.login-page {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
    "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}
```

### 7. 整体平滑过渡

- 给卡片、按钮、卖点卡、输入框统一加 `transition: all 0.2s ease;`，让 hover/focus 平滑。
- 标题字重可微调为 600（不要过粗），副标与描述用半透明灰白，营造轻盈感。

---

## 三、改动点 2：左侧卖点图标用「白底」衬托（解决看不清）

现状：图标是半透明色直接画在深紫背景上，对比不足。改为：**把每个卖点图标放进一个白色圆形（或圆角）底容器里，图标用品牌紫 `#6d5bd0`**，既清晰又贴合 iOS 圆角图标风格。

```css
.selling-point-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;          /* 圆形白底，iOS 风格；或 12px 圆角 */
  background: #fff;            /* 白底衬托图标 */
  color: #6d5bd0;              /* 图标品牌紫 */
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}
```

卖点卡内的结构调整为（图标 + 文字，横向排列）：
```html
<div class="selling-point-card">
  <span class="selling-point-icon"><Search :size="18" /></span>
  <span class="selling-point-text">证据可溯源</span>
</div>
```

图标沿用现有组件库（`lucide-vue-next`：`Search` / `ListChecks` / `Layers` 或 `@element-plus/icons-vue`），**不新增图片文件**。

> 补充：若左侧顶部 `PaperAgent` 的 Logo 图片在深紫背景上仍不够清晰，可同样用一个半透明白底圆形容器包裹（`border-radius:50%; background:rgba(255,255,255,.92)`），但**不替换 logo 图片本身**。

---

## 四、验收清单

1. 功能零改动（`script`、接口、路由、文案、Logo 均未变，可用 git diff 复核）。
2. 圆角明显加大（卡片 24px、输入框/按钮 14px），整体观感柔和圆润。
3. 阴影为多层柔和型，不再生硬；hover/focus 有平滑过渡。
4. 输入框为 iOS 浅灰内嵌底、聚焦紫描边。
5. 左侧渐变更柔和并带光晕；卖点卡有毛玻璃质感。
6. **三个卖点图标均为白底圆形、品牌紫图标，在深紫背景上清晰可辨**。
7. 响应式规则未变（<1024px 只显右侧表单）。
8. `vue-tsc` / `vite` 构建通过，无控制台报错。
