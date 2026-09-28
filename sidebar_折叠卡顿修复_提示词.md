# PaperAgent 侧边栏 · 卡顿修复提示词（移除重挂载 + Transition）

> 用途：修复侧边栏折叠按钮"点一下卡一下/闪一下"的问题。
> **根因**：`home.vue` 用 `<Transition name="slide">` 包裹 `<SideBar>` 且加了 `:key="'sidebar-'+isCollapsed"`，导致每次折叠切换时 Vue **销毁并重建整个侧边栏 DOM**，并叠加 700ms 滑入动画（leave 350ms → 重建 → enter 700ms），于是每次点击都明显卡顿、闪烁，hover 状态也丢失。
> 目标文件：`PaperQuery_Frontend/src/views/home.vue`（主改）、`PaperQuery_Frontend/src/App.vue`（可选清理）、`PaperQuery_Frontend/src/components/SideBar.vue`（可选小修）。

---

## 一、修复思路（核心原则）

**侧边栏应该常驻渲染，绝不能用 `:key` 强制重挂载。** 收起/展开只需「宽度平滑过渡 + 文字显隐」，已有 `.app-sidebar { transition: width .3s, flex-basis .3s }` 可平滑宽度。移除重挂载后即不再卡顿。

---

## 二、改动 1：`home.vue` — 移除 `<Transition>` 和 `:key`

**改前：**
```vue
<template>
  <div id="home" class="app-shell flex min-h-screen">
    <Transition name="slide">
      <SideBar
        :key="'sidebar-' + isCollapsed"
        :is-collapsed="isCollapsed"
        @toggle-collapse="isCollapsed = !isCollapsed"
      />
    </Transition>
    <router-view class="flex-grow" />
  </div>
</template>
```

**改后（SideBar 常驻，不再重建）：**
```vue
<template>
  <div id="home" class="app-shell flex min-h-screen">
    <SideBar
      :is-collapsed="isCollapsed"
      @toggle-collapse="isCollapsed = !isCollapsed"
    />
    <router-view class="flex-grow" />
  </div>
</template>
```

- 保留 `isCollapsed` 状态与切换逻辑。
- 侧边栏宽度变化由 `SideBar.vue` 里 `.app-sidebar` 已有的 `transition: width .3s ease-in-out, flex-basis .3s ease-in-out` 平滑过渡（已存在，无需重复加）。

---

## 三、改动 2（可选清理）：`App.vue` — 删除不再使用的 slide 全局样式

`home.vue` 移除 `<Transition name="slide">` 后，`App.vue` 里那组 `.slide-enter-active / .slide-leave-active / .slide-enter-from / .slide-leave-to / prefers-reduced-motion` 全局样式已无作用，建议一并删除，避免残留死代码。

---

## 四、改动 3（可选小修）：`SideBar.vue` — 收起后顶栏布局重叠隐患

当前收起态样式：
```css
.app-sidebar.collapsed .sidebar-topbar { justify-content: center; }
```
收起后 `sidebar-topbar` 里同时有 `brand`（品牌 Logo，`brand-copy` 已隐藏但 `brand-mark` 还在）和折叠按钮，两个都被居中排在一起，**可能重叠/挤在一起**。建议收起态让顶栏只居中折叠按钮，隐藏品牌块：

```css
.app-sidebar.collapsed .sidebar-topbar {
  justify-content: center;
}
.app-sidebar.collapsed .brand {
  display: none;   /* 收起后隐藏品牌块，只留折叠按钮居中，避免重叠 */
}
```

（若你希望收起后仍显示品牌小图标，可把 `brand` 与按钮纵向排布或用 `gap` 拉开，避免重叠；二选一即可。）

---

## 五、如果你仍想要"滑入"动画但不卡顿（可选方案）

不要用 `Transition` + `:key` 重挂载。改为给侧边栏**内部收起时会隐藏的文字**做纯 CSS 过渡（不销毁 DOM）：

```css
/* SideBar.vue scoped 内，替代「收起时 display:none」的文字块 */
.brand-copy,
.nav-label,
.nav-item span,
.sidebar-footer > div:last-child {
  transition: opacity .3s ease-in-out;
}
.app-sidebar.collapsed .brand-copy,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .nav-item span,
.app-sidebar.collapsed .sidebar-footer > div:last-child {
  opacity: 0;
}
```

> ⚠️ 注意：上面把 `display:none` 换成 `opacity:0` 后，这些元素仍占位（`nav-item` 的高度/文字宽度仍存在），需要配合 `width` 收缩或 `white-space:nowrap; overflow:hidden` 才能彻底收成图标栏。**若实现复杂，直接保留现有的 `display:none` 即可**——去掉 `Transition`/`:key` 后宽度过渡已经足够顺滑，卡顿问题已解决。此可选动画非必须。

---

## 六、验收清单

1. 点击三杠按钮，侧边栏**流畅收起/展开**（宽度平滑过渡），**不再卡顿、不再闪一下、不重建 DOM**。
2. 收起后只留图标，展开后恢复文字；hover 状态在收起/展开过程中正常保留。
3. 右侧内容（Dashboard 卡片等）随侧边栏宽度自动适配，无错位、无横向溢出。
4. 品牌 Logo、导航项、路由、底部"服务正常 / DeepSeek 已连接"、导航高亮均未变。
5. ≤900px 窄栏、≤560px 底部导航原有响应式行为不受影响。
6. `App.vue` 残留的 slide 样式（若删除）不影响其他功能。
7. `vue-tsc` / `vite` 构建通过，无控制台报错。
