# PaperAgent 登录页 · 增补提示词 ⑤（登录失败弹窗淡入上滑动画）

> 用途：给登录页「登录失败 / 账户或密码不存在」的弹窗（`ElNotification`）加一个**淡入 + 上滑**的进场动画。**仅改样式（动画），弹窗从哪里出来（位置）保持不变**；功能、文字、逻辑、新拟物风格均不变。
> 目标文件：`PaperQuery_Frontend/src/views/login/login.vue`。

---

## 一、现状（已核实）

- 登录失败弹窗在 `src/views/login/login.vue` 的两处 `catch` 分支里用 **`ElNotification`** 弹出（`type:'error'`，`title:'登录失败'`），默认出现在**右上角**（position 默认 `'top-right'`）。
- `ElNotification` 是 **teleport 到 `body` 下**渲染的，因此 `login.vue` 里的 `<style scoped>` **命中不到弹窗元素**。要改弹窗动画，动画规则必须放在**非 scoped 的全局 `<style>` 块**（或全局样式文件）里。

---

## 二、功能与内容红线（不变）

- **不改** `script` 逻辑：`Login()` 函数、`ElNotification` 的调用、`title`/`type`/`message`、`router.push('/home')`、catch 分支全部保留。
- **不改弹窗位置**：`position` 参数保持默认右上角（**不要**传 `position:'bottom-right'` 等，也不要改动来源方向）。
- **不改**登录表单、字段、Logo、主色 `#6d5bd0`、新拟物风格、左右分栏与响应式。
- 你只允许：给 `ElNotification` 加一个 `customClass`，并在文件内新增一个**非 scoped** `<style>` 块写动画。

---

## 三、改动步骤

### 1. 给登录失败（建议也含成功）的 ElNotification 加自定义类

在 `login.vue` 中，把两处失败弹窗（以及可选的 `登录成功` 弹窗）配置里各加一个字段 `customClass`：

```ts
ElNotification({
  title: '登录失败',
  type: 'error',
  message: error.message,
  customClass: 'login-notify-fade-up',   // 新增：挂自定义类，用于命中动画
})
```

（成功弹窗同样加 `customClass: 'login-notify-fade-up'`，保持风格统一；若只想失败弹窗有动画，则只加失败两处。）

### 2. 在文件底部新增一个【非 scoped】 `<style>` 块（关键）

因为弹窗 teleport 到 body，`<style scoped>` 命中不到。请在 `login.vue` 末尾**追加一个不带 `scoped` 的 `<style>` 块**（或在全局样式文件里加同样内容），写入淡入上滑动画：

```css
/* 登录弹窗：淡入 + 上滑（覆盖 element-plus 默认进场动画，不改位置） */
.login-notify-fade-up {
  animation-name: login-notify-fade-in-up !important;
  animation-duration: 600ms !important;
  animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1) !important;
  animation-fill-mode: both !important;
}

@keyframes login-notify-fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);   /* 只做纵向位移，不影响右上角来源位置 */
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 可访问性：用户开启“减少动态效果”时关闭动画 */
@media (prefers-reduced-motion: reduce) {
  .login-notify-fade-up {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
}
```

> 说明：
> - `!important` 是为了覆盖 element-plus 自带的进场动画类（如 `.el-notification-fade-enter-active`）。
> - `transform: translateY(20px)` 只是**元素自身从下方上滑到位的位移**，不是改变弹窗在屏幕上的来源位置（仍固定在右上角弹出），符合"从哪里出来不要改"的要求。
> - 动画时长如想更快/更慢，改 `animation-duration`（例如 `1000ms` 配 `cubic-bezier(0.33,1,0.68,1)`）。

---

## 四、验收清单

1. 输入错误账号密码，登录失败弹窗**淡入 + 上滑**进入，来源位置仍在**右上角**（未改变）。
2. `script` 逻辑零改动（`git diff` 复核 `Login()` 与 `ElNotification` 调用），只新增了 `customClass` 字段。
3. 弹窗动画规则位于**非 scoped** `<style>` 块（或全局样式），能命中 body 下 teleport 元素。
4. 新拟物风格、登录表单、Logo、主色 `#6d5bd0`、分栏与响应式均未变。
5. `prefers-reduced-motion: reduce` 时动画关闭、弹窗正常显示。
6. `vue-tsc` / `vite` 构建通过，无控制台报错。
