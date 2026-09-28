# PaperAgent 登录页优化 · 方案 B（分栏产品叙事）· 给 Trae 的修改提示词

> 用途：将登录页从「单栏居中卡片」改造为「左右分栏的产品叙事布局」，视觉升级，**功能完全不变**。
> 目标文件：`PaperQuery_Frontend/src/views/login/login.vue`（只改这一个文件）。
> 设计参考：方案 B 设计稿（左：紫渐变品牌叙事区；右：纯白登录表单区）。

---

## 一、任务目标

把现有登录页升级为**左右分栏**布局：
- **左侧**：紫色渐变品牌叙事区，展示产品定位（可信智能研究工作台）、副标语、功能卖点、英文标语；
- **右侧**：保留原有登录表单卡片（欢迎回来 / 用户名 / 密码 / 登录 / 本地体验账号提示）。

页面整体配色沿用项目现有品牌色（主紫 `#6d5bd0`、hover `#5e4bc2`）、浅灰底、白色卡片、系统无衬线字体、圆角 `16px`（卡片）/ `9px`（输入框与按钮）。

---

## 二、【最高优先级】功能红线 —— 以下内容一律不许改动

1. **不改任何 script 逻辑**：`username`、`password`、`url` 三个 `ref` 的声明与默认值（`url` 默认 `http://localhost:8001`）不动；`login()` 函数、`ElNotification` 成功/失败提示、`router.push('/home')` 全部原样保留。
2. **不改任何登录校验与提交行为**：表单仍 `@submit.prevent="Login"`，字段仍 `required`，`autocomplete` 属性保留。
3. **不改接口**：后端登录接口 `@/api/auth` 的 `login(url, user)` 调用方式不变。
4. **不改路由**：登录成功仍跳 `/home`。
5. **字段文案保持**：标签「用户名」「密码」、占位「请输入用户名」「请输入密码」、按钮「登录」、底部「本地体验账号：admin / 123456」、英文标语 `Your private workspace for academic discovery.` 全部保留。
6. **Logo 必须沿用**：继续使用 `@/assets/img/paperagent-mark.png`（`paperAgentMark`），**不得替换、不得重绘、不得删除**。

> 结论：你只允许修改**模板的结构布局**和 **`<style scoped>` 的样式**，以及为了承载新布局而新增的纯展示 DOM；禁止触碰 `script` 与任何功能逻辑。

---

## 三、当前文件关键现状（改动前基线）

```vue
<script setup lang="ts">
import { login } from '@/api/auth'
import paperAgentMark from '@/assets/img/paperagent-mark.png'
const username = ref('')
const password = ref('')
const router = useRouter()
const url = ref('http://localhost:8001')
const Login = async () => { /* 成功→ElNotification+router.push('/home')；失败→ElNotification */ }
</script>

<template>
  <main class="login-page">
    <section class="login-shell">
      <div class="brand-header">
        <img :src="paperAgentMark" alt="PaperAgent 标志" />
        <div><h1>PaperAgent</h1><p>阅读、理解与研究你的论文</p></div>
      </div>
      <Card class="login-card">
        <form @submit.prevent="Login">
          <CardHeader>
            <CardTitle>欢迎回来</CardTitle>
            <p class="card-description">登录后继续访问你的论文库与研究任务</p>
          </CardHeader>
          <CardContent>
            <!-- 用户名输入 -->
            <!-- 密码输入 -->
          </CardContent>
          <CardFooter class="login-footer">
            <Button type="submit" class="login-button">登录</Button>
            <p>本地体验账号：admin / 123456</p>
          </CardFooter>
        </form>
      </Card>
      <p class="product-note">Your private workspace for academic discovery.</p>
    </section>
  </main>
</template>

<style scoped>
/* 现有样式：.login-page 浅灰底 #f7f7f8 居中；.brand-header 顶部 logo+标题；
   .login-card 白卡片 16px 圆角；.login-button 紫 #6d5bd0 通栏；.product-note 灰色小字 */
</style>
```

---

## 四、具体改造步骤（全部作用于 login.vue）

### 1. 布局结构改为左右分栏

把 `.login-shell` 从「单一居中列」改为「左右两栏」：
- 外层 `.login-shell` 使用 `display:flex`（或 grid），**横屏（≥1024px）时左右分栏，左侧约 55%、右侧约 45%**，铺满视口高度。
- **左侧品牌区**：新增一个 `.brand-panel` 容器，深紫渐变背景，负责品牌叙事。
- **右侧表单区**：原有 `.login-card` 迁移到右侧白色区域，垂直居中。

### 2. 左侧品牌区内容（`<div class="brand-panel">`）

从上到下依次布局（左对齐，白色文字）：
1. **顶部 Logo + 字标**：沿用 `paperAgentMark` 图片 + 白色粗体「PaperAgent」。
   - 若该 logo 在深紫背景上对比不足，可用一个**白色/半透明白色圆底容器**包裹图片（如 `border-radius:9999px; background:rgba(255,255,255,.95)`），**不得替换或重绘 logo 本身**。
2. **主标题**：白色大号标题「可信智能研究工作台」（`font-weight:600~700`）。
3. **副标题**：白色半透明小字「阅读、理解与研究你的论文」。
4. **功能卖点卡片**：纵向排列 **3 张** 半透明毛玻璃质感的小卡片，每张含一个图标 + 一行白字说明。建议文案（纯展示、不绑定任何事件）：
   - 「证据可溯源」
   - 「混合检索问答」
   - 「科研任务编排」
5. **底部英文标语**：白色半透明小字 `Your private workspace for academic discovery.`（可吸底）。

> ⚠️ 卖点卡片是**纯视觉装饰**，不得添加点击事件、hover 交互、路由跳转或任何动态逻辑；不得引入新页面。

### 3. 右侧表单区

- 把原有 `.brand-header`（顶部居中的 logo + 标题）**移除**，因为它会被左侧品牌区替代（logo 已在左侧沿用）。
- 保留 `.login-card` 的完整内容：`欢迎回来` 标题、`登录后继续访问你的论文库与研究任务` 描述、用户名/密码输入、登录按钮、`本地体验账号：admin / 123456`。
- 表单卡片在右侧白色区域**垂直居中**，卡片保持白底、`16px` 圆角、柔和阴影、浅灰边框。

### 4. 响应式降级（重要）

- **移动端 / <1024px**：左侧 `.brand-panel` **隐藏**（`display:none`），只显示右侧登录表单，整体回到「单栏居中卡片」形态（近似现有布局），保证小屏可用。
- 可用 tailwind 响应式类实现（项目已装 tailwindcss `^3.4.4`），例如左侧 `hidden lg:flex lg:w-[55%]`、右侧 `w-full lg:w-[45%]`。

### 5. 样式与设计 token（沿用项目现有体系）

| 项 | 值 |
|---|---|
| 主紫 | `#6d5bd0`，hover `#5e4bc2` |
| 左区渐变 | `linear-gradient(160deg,#6d5bd0,#4a3f9a)`（或 `#6d5bd0 → #4a3f9a`） |
| 右区背景 | `#f7f7f8`（沿用现有 `--c-bg` 风格） |
| 卡片 | 白底、`border:1px solid #e1e1e3`、`border-radius:16px`、柔和阴影 |
| 输入框 | 高 `44px`、`border-radius:9px`、浅灰边框（沿用现有） |
| 按钮 | 通栏、高 `43px`、`border-radius:9px`、主紫底、白字（沿用现有，可改渐变 `#6d5bd0→#8b7ee6`，可选） |
| 字体 | 沿用项目系统字体栈（无需改） |
| 卖点卡 | 半透明白 `rgba(255,255,255,.08~.14)`、`backdrop-filter:blur()`（可选）、`border-radius:12px` |

### 6. 图标来源（不新增图片文件）

功能卖点卡的图标**不要新增图片**，改用项目已安装的图标组件库，例如：
- `lucide-vue-next`（已装 `^0.407.0`）：如 `Search`、`FileText`、`Layers`、`ListChecks` 等；
- 或 `@element-plus/icons-vue`（已装）。

示例（lucide）：
```vue
<script setup>
import { Search, ListChecks, Layers } from 'lucide-vue-next'
</script>
```
在左侧三个卖点卡片里分别放一个图标组件即可。若某个图标库在 `<script setup>` 中未注册，请按项目内既有用法（`unplugin-vue-components` 自动导入或显式 import）接入。

---

## 五、新增资源说明（重要）

- **本次改造不需要新增任何图片资源**（无新 png/jpg/svg 文件）。
- 所有图标用现有图标组件库；背景用 CSS 渐变与伪元素。
- Logo 沿用现有 `src/assets/img/paperagent-mark.png`，路径与 import 不变。
- 若你（Trae）认为需要额外背景纹理，用 CSS 渐变 + `radial-gradient` 光晕即可，不要引入外部图片。

---

## 六、验收清单（完成后逐项自查）

1. 登录功能与之前完全一致：输入 admin/123456 可登录成功并跳转 `/home`；错误账号弹失败提示。
2. `script` 逻辑未被改动（可对比 git diff，`login()` 等函数零改动）。
3. Logo 仍是 `paperagent-mark.png`，未被替换或重绘。
4. 横屏 ≥1024px 为左右分栏；<1024px 只显示右侧表单（左侧隐藏）。
5. 左右分栏视觉符合方案 B 设计稿（左紫渐变品牌区 + 右白底表单，卖点卡 3 张）。
6. 表单字段、按钮、本地体验账号提示、英文标语文案未改动。
7. 无新增图片文件；图标来自现有组件库。
8. 页面无控制台报错，`vue-tsc`/`vite` 构建通过。

---

## 七、设计稿参考

以「方案 B · 分栏产品叙事」预览图为视觉基准。若交付时无法对照图片，按本文第四节的布局与颜色描述实现即可。
