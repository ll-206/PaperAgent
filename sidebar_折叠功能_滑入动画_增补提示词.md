# PaperAgent 侧边栏 · 增补提示词（折叠滑入动画 slide-in-left）

> 用途：在**已实现的侧边栏折叠功能**基础上，给侧边栏的展开/收起加上 **`slide-in-left`（从左滑入 + 淡入）** 动画。**不新增功能、不改导航/路由/Logo/底部状态**，只加动画与过渡。
> 目标文件：`PaperQuery_Frontend/src/views/home.vue`、`PaperQuery_Frontend/src/components/SideBar.vue`。

---

## 一、动画目标

- **展开时**：侧边栏从左滑入并淡入到位——`translateX(-30px) + opacity:0` → `translateX(0) + opacity:1`。
- **收起时**：可选反向滑出（`translateX(0)` → `translateX(-30px)` + 淡出），保持顺滑。
- 时长 `700ms`，缓动 `cubic-bezier(0.16, 1, 0.3, 1)`（对应你给的模板）。
- 开启 `prefers-reduced-motion` 时关闭动画。

---

## 二、关键点（为什么用 Transition + :key）

- 侧边栏**常驻渲染**（收起后仍保留窄图标栏），仅靠 class 切换宽度，**不会触发 CSS `animation` 重播**。
- 要让它"滑入"，最可靠的方式是用 Vue 的 `<Transition>` 包裹侧边栏，并在折叠状态切换时**用 `:key` 强制重挂载**，从而播放进入过渡动画。

---

## 三、改动 1：`home.vue` — 用 `<Transition>` 包裹侧边栏并加 `:key`

```vue
<template>
  <div id="home" class="app-shell flex min-h-screen">
    <Transition name="slide">
      <SideBar
        :key="'sidebar-' + isCollapsed"   <!-- 折叠状态变化 → 重挂载 → 播放滑入动画 -->
        :is-collapsed="isCollapsed"
        @toggle-collapse="isCollapsed = !isCollapsed"
      />
    </Transition>
    <router-view class="flex-grow" />
  </div>
</template>
```

> 说明：`:key` 随 `isCollapsed` 变化，Vue 会销毁并重建 SideBar 根组件，重建后仍按当前 `isCollapsed` 渲染（收起时仍是窄图标栏），同时触发 `<Transition>` 的进入动画 `slide-in-left`。收起时同理重放滑出/滑入过渡。

---

## 四、改动 2：滑入过渡样式（放**全局 / 非 scoped** 样式）

`<Transition name="slide">` 的过渡类会加在 **SideBar 根元素**上，`home.vue` 的 `<style scoped>` 用普通选择器命中不到子组件根。请把以下样式放到**全局样式**（如 `src/App.vue` 的非 scoped `<style>`、`src/assets/index.css`、或 `main.ts` 引入的全局 css），或用 `:deep()`：

```css
/* slide-in-left：从左滑入 + 淡入 */
.slide-enter-active {
  transition:
    opacity 700ms cubic-bezier(0.16, 1, 0.3, 1),
    transform 700ms cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-leave-active {
  transition:
    opacity 350ms ease,
    transform 350ms ease;
}
.slide-enter-from {
  opacity: 0;
  transform: translateX(-30px);   /* 从左侧进入 */
}
.slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);   /* 向左滑出 */
}

/* 可访问性：减少动态效果时关闭 */
@media (prefers-reduced-motion: reduce) {
  .slide-enter-active,
  .slide-leave-active {
    transition: none !important;
  }
}
```

> 若你想严格用 `@keyframes slide-in-left` 而非 transition，也可写：
> ```css
> .slide-enter-active { animation: slide-in-left 700ms cubic-bezier(0.16,1,0.3,1) 0ms both; }
> .slide-leave-active { animation: slide-out-left 350ms ease both; }
> @keyframes slide-in-left { from { opacity:0; transform:translateX(-30px); } to { opacity:1; transform:translateX(0); } }
> @keyframes slide-out-left { from { opacity:1; transform:translateX(0); } to { opacity:0; transform:translateX(-30px); } }
> ```
> 两种实现二选一，推荐 transition 版本（更稳、复用既有模板语义）。

---

## 五、可选增强：收起/展开的宽度平滑过渡

若希望侧边栏**变窄/变宽**的过程也顺滑（配合滑入更自然），给 `SideBar.vue` 的 `.app-sidebar` 加：

```css
.app-sidebar {
  transition: width 0.3s ease-in-out, flex-basis 0.3s ease-in-out;
}
```

---

## 六、验收清单

1. 点击三杠按钮，侧边栏从左侧滑入（`-30px → 0` + 淡入），宽度随之变化。
2. 再点击收起，侧边栏滑出/变窄，只留图标；再次点击可展开并重新滑入。
3. 收起后右侧内容（Dashboard 卡片等）自动适配、无错位、无横向溢出。
4. 品牌 Logo、导航项、路由、底部"服务正常 / DeepSeek 已连接"、导航高亮均未变。
5. 折叠功能本身（`isCollapsed` 切换、窄图标栏样式）未回退。
6. `prefers-reduced-motion` 下动画关闭、侧边栏正常显示。
7. 滑入过渡类位于全局/非 scoped 样式（能命中 SideBar 根元素）；`vue-tsc` / `vite` 构建通过，无控制台报错。
