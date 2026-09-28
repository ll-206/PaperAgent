# PaperAgent 侧边栏 · 收起文字平滑过渡修复提示词

> 用途：修复侧边栏**收起（滑出）时文字显示突兀/不协调**的问题。
> **根因**：收起态用 `display:none` 瞬间隐藏文字（`SideBar.vue` 第 77–81 行），而 `.app-sidebar` 的宽度是 `0.3s` 过渡。宽度有动画、文字与图标居中布局却瞬间切换，两者不同步 → 滑出过程中文字突然消失、图标瞬间居中、布局跳变。
> 目标文件：`PaperQuery_Frontend/src/components/SideBar.vue`（仅样式）。

---

## 一、修复思路

让收起/展开时**文字跟随宽度一起平滑过渡**：用 `opacity` + `max-width` 过渡替代 `display:none` 的瞬间切换，使文字在滑出时淡出并收缩、图标平滑居中；展开时反向淡入。核心是处理 `nav-item` 文字的占位（否则图标无法真正居中）。

---

## 二、改动：`SideBar.vue` `<style scoped>` — 把收起态的 `display:none` 改为过渡

### 1. 先给需要显隐的元素加过渡基础

在 `.nav-item`、`.brand-copy`、`.nav-label`、`.sidebar-footer` 相关文字上加 `transition`：

```css
/* 导航项文字：淡出 + 宽度收缩（关键，保证收起后图标真正居中） */
.nav-item {
  gap: 12px;                    /* 展开态间距 */
  transition: gap .3s ease-in-out, background .15s;
}
.nav-item span {
  white-space: nowrap;
  overflow: hidden;
  transition: opacity .3s ease-in-out, max-width .3s ease-in-out;
}

/* 品牌字标 / WORKSPACE 标签 / 底部状态文字：淡出即可 */
.brand-copy,
.nav-label,
.sidebar-footer > div:last-child {
  transition: opacity .3s ease-in-out;
}
```

### 2. 收起态：文字淡出 + 收缩（替代原来的 `display:none`）

把原来的：
```css
.app-sidebar.collapsed .brand-copy,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .nav-item span,
.app-sidebar.collapsed .nav-item.active i,
.app-sidebar.collapsed .sidebar-footer > div:last-child { display: none; }
```
替换为：
```css
.app-sidebar.collapsed .nav-item {
  gap: 0;                       /* 收起时间距收缩，图标居正中 */
}
.app-sidebar.collapsed .nav-item span {
  opacity: 0;
  max-width: 0;                 /* 文字宽度收缩为 0，不占位 */
  margin: 0;
}
.app-sidebar.collapsed .brand-copy,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .sidebar-footer > div:last-child {
  opacity: 0;                   /* 淡出（栏已收窄，块级占位可接受） */
}
.app-sidebar.collapsed .nav-item.active i {
  opacity: 0;
}
```

### 3. 可选：彻底不占位（若你担心文字淡出后仍占高度）

如果希望淡出后完全不占布局，可在收起态把这些文字**在淡出完成后隐藏**，用 `visibility:hidden` 与 `transition` 配合（`visibility` 支持延迟切换，能在过渡结束后生效）：

```css
.app-sidebar.collapsed .nav-item span,
.app-sidebar.collapsed .brand-copy,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .sidebar-footer > div:last-child {
  opacity: 0;
  visibility: hidden;           /* 过渡结束后不占交互、不再影响布局 */
  transition: opacity .3s ease-in-out, visibility 0s linear .3s;
}
```

> 说明：`visibility` 的 `transition ... 0s linear .3s` 让它在 `opacity` 淡出完成后才切到 `hidden`，实现"先淡出、后隐藏"，既平滑又不残留占位。若嫌复杂，用上面第 2 步的纯 `opacity`+`max-width` 方案即可（`nav-item span` 已用 `max-width:0` 处理占位，主要占位问题已解决）。

---

## 三、验收清单

1. 收起（滑出）时，文字平滑淡出并收缩，图标平滑居中，**不再突然消失/跳变**；展开时文字平滑淡入。
2. 收起后侧边栏只留图标、无文字残留、无文字溢出到栏外。
3. 宽度过渡（0.3s）与文字过渡（0.3s）节奏一致、无明显错位。
4. 品牌 Logo、导航项、路由、底部状态、导航高亮均未变；hover 正常。
5. 点击响应流畅，**无卡顿**（未重新引入重挂载/Transition）。
6. ≤900px 窄栏、≤560px 底部导航行为不受影响；`vue-tsc` / `vite` 构建通过。
