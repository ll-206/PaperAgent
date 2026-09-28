# PaperAgent 侧边栏折叠功能 · Trae 提示词

> 用途：给 Dashboard 主界面左侧边栏加**折叠/展开**功能——在侧边栏右上角放一个「三杠」按钮，点击后侧边栏收起只留图标，再次点击图标恢复展开；收起后右侧内容自动适配。
> 目标文件：`PaperQuery_Frontend/src/components/SideBar.vue`、`PaperQuery_Frontend/src/views/home.vue`（两个文件）。
> 风格：沿用现有 SideBar 的浅灰新拟物/扁平样式与品牌紫 `#6d5bd0` 强调色，不引入新 UI 组件库。

---

## 一、现状（已核实代码）

- 主布局 `src/views/home.vue`：
  ```vue
  <div id="home" class="app-shell flex min-h-screen">
    <SideBar :is-collapsed="isCollapsed" />
    <router-view class="flex-grow" />
  </div>
  <script setup lang="ts">
  const isCollapsed = ref(false)   // 折叠状态已在 home.vue，但无人切换、无样式生效
  </script>
  ```
  **右侧内容是 `<router-view class="flex-grow">`（flex 弹性项）**，因此只要侧边栏宽度变化，右侧会自动撑满剩余空间——**无需改右侧布局**。
- `src/components/SideBar.vue`：已接收 `isCollapsed` prop，模板根节点已有 `:class="{ collapsed: isCollapsed }"`，但**没有折叠按钮、没有切换事件、也没有 `.collapsed` 的收起样式**（`isCollapsed` 目前形同虚设）。
- 侧边栏当前结构：`brand`（Logo+字标）→ `nav-label`（WORKSPACE）→ `nav-list`（5 个导航项）→ `sidebar-footer`（服务状态）。
- 现有响应式已含 `@media(max-width:900px)` 的窄栏（76px 只留图标）样式，可作为 `.collapsed` 样式的参考。

---

## 二、功能与内容红线（不变）

- **不改**导航项、路由、品牌 Logo（`paperagent-mark.png`）、底部状态（服务正常 / DeepSeek 已连接）。
- **不改** `home.vue` 的 flex 布局结构（右侧自动适配是它的天然能力）。
- **不改**现有响应式规则（≤900px 自动窄栏、≤560px 底部导航）。
- 只**新增**：折叠按钮、切换逻辑、`.collapsed` 收起样式。不新增页面/路由/接口。

---

## 三、改动 1：`SideBar.vue` — 加右上角「三杠」按钮 + 触发切换

### 1. 模板：在 `brand` 行的右侧放折叠按钮

把现有 `brand` 结构改为可容纳按钮（按钮靠右）：

```vue
<nav class="app-sidebar" :class="{ collapsed: isCollapsed }">
  <div class="sidebar-topbar">
    <router-link to="/home/dashboard" class="brand">
      <span class="brand-mark"><img :src="paperAgentMark" alt="" /></span>
      <span class="brand-copy"><strong>PaperAgent</strong></span>
    </router-link>
    <button
      type="button"
      class="collapse-toggle"
      :aria-label="isCollapsed ? '展开侧边栏' : '收起侧边栏'"
      @click="emit('toggleCollapse')"
    >
      <Menu :size="18" />
    </button>
  </div>
  <!-- nav-label / nav-list / sidebar-footer 保持不变 -->
</nav>
```

> 说明：`Menu` 是 lucide-vue-next 的三杠（汉堡）图标，正好符合"三杠按钮"需求。若想收起/展开用不同图标，可 `isCollapsed ? <PanelLeft/> : <Menu/>`，但默认统一用三杠 `Menu` 即可。

### 2. 脚本：接收 prop 并声明 emit

```ts
import { Menu } from 'lucide-vue-next'

defineProps({
  isCollapsed: Boolean,
})

const emit = defineEmits<{ (e: 'toggleCollapse'): void }>()
```

（保留现有 `sidebarItems`、`CircleCheck`、`paperAgentMark` 导入与 `isActive` 逻辑不变。）

### 3. 样式：给 topbar / 按钮加样式，并定义 `collapsed` 收起样式

在 `<style scoped>` 追加：

```css
/* 顶栏：让按钮靠右 */
.sidebar-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.collapse-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 9px;
  color: #4f5054;
  background: transparent;
  cursor: pointer;
  transition: background .15s, color .15s;
}
.collapse-toggle:hover {
  color: #202123;
  background: #ededee;
}

/* ===== 折叠态：收起为窄栏，只留图标 ===== */
.app-sidebar.collapsed {
  flex-basis: 76px;
  width: 76px;
  padding: 18px 11px;
}
.app-sidebar.collapsed .brand {
  justify-content: center;
  padding-bottom: 24px;
}
.app-sidebar.collapsed .brand-copy,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .nav-item span,
.app-sidebar.collapsed .nav-item.active i,
.app-sidebar.collapsed .sidebar-footer > div:last-child {
  display: none;   /* 隐藏文字，只留图标 */
}
.app-sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}
.app-sidebar.collapsed .nav-item svg {
  margin: 0;
}
.app-sidebar.collapsed .sidebar-footer {
  justify-content: center;
  padding: 8px;
}
/* 折叠时按钮仍保留在顶栏，便于再次点击恢复 */
.app-sidebar.collapsed .sidebar-topbar {
  justify-content: center;
}
```

---

## 四、改动 2：`home.vue` — 监听切换事件

```vue
<template>
  <div id="home" class="app-shell flex min-h-screen">
    <SideBar :is-collapsed="isCollapsed" @toggle-collapse="isCollapsed = !isCollapsed" />
    <router-view class="flex-grow" />
  </div>
</template>
```

> `router-view` 是 `flex-grow`，侧边栏从 `224px` 变 `76px` 后，右侧内容**自动填充剩余宽度并重新排版**——不需要额外改右侧任何页面。

---

## 五、右侧内容适配说明（重要）

- 右侧内容**不需要**改：`home.vue` 是 `flex` 布局，`<SideBar>` 是固定宽度弹性项，`<router-view>` 是 `flex-grow`。侧边栏收起变窄后，右侧自动占满剩余空间。
- 各子页面（dashboard / chat / library / forum / research 等）本身是响应式布局，宽度变宽后正常铺满，无需逐页适配。
- 折叠/展开时若希望右侧内容过渡平滑，可给 `router-view` 加 `transition`，但**可选**，不是必须。

---

## 六、响应式兼容

- 保留现有 `@media(max-width:900px)` 窄栏与 `@media(max-width:560px)` 底部导航逻辑不变。
- 折叠按钮仅在 >900px 的宽屏有意义（窄屏本身已是图标栏）。`collapsed` 样式与现有 ≤900px 窄栏样式一致，可复用其隐藏规则，避免重复定义冲突。

---

## 七、验收清单

1. 宽屏下侧边栏右上角出现三杠按钮，点击后侧边栏收起为窄栏（只留各导航图标），再点击恢复展开。
2. 收起/展开过程中，右侧内容（Dashboard 统计卡片等）自动适配新宽度、无横向溢出、无错位。
3. 品牌 Logo、导航项、路由、底部"服务正常 / DeepSeek 已连接"均未改变、仍可点击跳转。
4. 导航高亮（active）逻辑未变。
5. `script` 中除新增 `emit` 与 `Menu` 导入外无其他改动；`git diff` 复核。
6. ≤900px 窄栏、≤560px 底部导航原有行为不受影响。
7. `vue-tsc` / `vite` 构建通过，无控制台报错。
