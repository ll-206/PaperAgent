<script setup lang="ts">
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { ElNotification } from 'element-plus'
import { login } from '@/api/auth'
import paperAgentMark from '@/assets/img/paperagent-mark.png'

const username = ref('')
const password = ref('')
const router = useRouter()

const url = ref('http://localhost:8001')

// 向后端发送登录请求并将用户信息存储到 Vuex 和 localStorage 中
const Login = async () => {
  const user = {
    username: username.value,
    password: password.value,
  }

  try {
    await login(url.value, user)
    ElNotification({
      title: '登录成功',
      type: 'success',
    })
    router.push('/home')
  } catch (error) {
    if (error instanceof Error) {
      ElNotification({
        title: '登录失败',
        type: 'error',
        message: error.message,
      })
      console.error('登录失败:', error)
    } else {
      // 处理非 Error 对象的情况
      ElNotification({
        title: '登录失败',
        type: 'error',
        message: '发生未知错误',
      })
    }
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-shell">
      <div class="brand-header">
        <img :src="paperAgentMark" alt="PaperAgent 标志" />
        <div>
          <h1>PaperAgent</h1>
          <p>阅读、理解与研究你的论文</p>
        </div>
      </div>

      <Card class="login-card">
      <form @submit.prevent="Login">
        <CardHeader>
          <CardTitle>欢迎回来</CardTitle>
          <p class="card-description">登录后继续访问你的论文库与研究任务</p>
        </CardHeader>

        <CardContent>
          <div class="grid items-center w-full gap-4">
            <!-- <div class="flex flex-col space-y-1.5">
              <Label for="url">网址</Label>
              <Input id="url" v-model="url" placeholder="url" required />
            </div> -->
            <div class="flex flex-col space-y-1.5">
              <Label for="username">用户名</Label>
              <Input
                id="username"
                v-model="username"
                placeholder="请输入用户名"
                autocomplete="username"
                required
              />
            </div>
            <div class="flex flex-col space-y-1.5">
              <Label for="password">密码</Label>
              <Input
                id="password"
                v-model="password"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
                required
              />
            </div>
          </div>
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
.login-page { display: grid; width: 100%; min-height: 100vh; place-items: center; padding: 28px; color: #202123; background: #f7f7f8; }
.login-shell { width: 100%; max-width: 390px; }
.brand-header { display: flex; align-items: center; justify-content: center; gap: 13px; margin-bottom: 28px; }.brand-header img { width: 52px; height: 52px; object-fit: contain; }.brand-header h1,.brand-header p { margin: 0; }.brand-header h1 { font-size: 25px; font-weight: 650; letter-spacing: -.035em; }.brand-header p { margin-top: 3px; color: #77777c; font-size: 12px; }
.login-card { width: 100%; border: 1px solid #e1e1e3; border-radius: 16px; background: #fff; box-shadow: 0 10px 35px rgba(0,0,0,.055); }.login-card :deep(h3) { font-size: 19px; font-weight: 600; }.card-description { margin: 5px 0 0; color: #85858a; font-size: 12px; line-height: 1.5; }.login-card :deep(input) { height: 44px; border-radius: 9px; }
.login-footer { display: flex; flex-direction: column; gap: 12px; padding: 0 24px 24px; }.login-button { width: 100%; height: 43px; border-radius: 9px; color: #fff; background: #6d5bd0; }.login-button:hover { background: #5e4bc2; }.login-footer p { margin: 0; color: #9a9a9f; font-size: 10px; text-align: center; }
.product-note { margin: 20px 0 0; color: #a0a0a5; font-size: 10px; letter-spacing: .04em; text-align: center; }
@media (max-width:480px) { .login-page { padding: 18px; }.brand-header { margin-bottom: 22px; }.login-card { border-radius: 14px; box-shadow: none; } }
</style>
