<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElNotification } from 'element-plus'
import {
  createResearchTask,
  listResearchTasks,
  getResearchTask,
} from '@/api/research'
import ArtifactPanel from './components/ArtifactPanel.vue'

interface TaskItem {
  task_id: string
  goal: string
  status: string
  mode: string
}

interface StepInfo {
  step_id: string
  title?: string
  skill_name: string
  status: string
  error?: string
  duration_ms?: number
}

interface ArtifactInfo {
  artifact_id: string
  type: string
  title: string
  data?: Record<string, any>
}

interface TaskDetail {
  task_id: string
  goal: string
  status: string
  plan?: { steps: Array<{ step_id: string; title: string; skill: string }> }
  steps: StepInfo[]
  artifacts: ArtifactInfo[]
}

const goal = ref('')
const creating = ref(false)
const tasks = ref<TaskItem[]>([])
const currentTask = ref<TaskDetail | null>(null)
const loadingDetail = ref(false)

const loadTasks = async () => {
  try {
    const resp = await listResearchTasks()
    if (resp?.data) {
      tasks.value = resp.data
    }
  } catch (e: any) {
    console.error(e)
  }
}

const handleCreate = async () => {
  if (!goal.value.trim()) return
  creating.value = true
  try {
    const resp = await createResearchTask(goal.value.trim())
    if (resp?.data) {
      ElNotification.success(`任务已创建：${resp.data.task_id}`)
      await loadTasks()
      await selectTask(resp.data.task_id)
    }
  } catch (e: any) {
    ElNotification.error({ title: '创建失败', message: e.message || '任务创建失败' })
  } finally {
    creating.value = false
  }
}

const selectTask = async (taskId: string) => {
  loadingDetail.value = true
  try {
    const resp = await getResearchTask(taskId)
    if (resp?.data) {
      currentTask.value = resp.data
    }
  } catch (e: any) {
    ElNotification.error({ title: '加载失败', message: e.message || '任务详情加载失败' })
  } finally {
    loadingDetail.value = false
  }
}

const statusType = (status: string) => {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILED') return 'danger'
  return 'info'
}

onMounted(() => {
  loadTasks()
})
</script>

<template>
  <div class="flex-col w-full p-8">
    <h1 class="text-2xl font-bold mb-6">Research Workspace</h1>

    <!-- 创建任务 -->
    <div class="flex space-x-4 mb-8">
      <el-input
        v-model="goal"
        type="textarea"
        :rows="2"
        class="flex-1"
        placeholder="输入科研目标，例如：检索并比较相关论文的方法与数据集，生成一份综述报告"
      />
      <el-button
        type="primary"
        :disabled="!goal.trim() || creating"
        :loading="creating"
        @click="handleCreate"
      >
        开始研究
      </el-button>
    </div>

    <div class="flex space-x-6">
      <!-- 历史任务 -->
      <div class="w-1/3">
        <h2 class="text-lg font-semibold mb-3">历史任务</h2>
        <div v-if="tasks.length === 0" class="text-gray-400 text-sm">
          暂无任务，输入目标开始研究
        </div>
        <div
          v-for="t in tasks"
          :key="t.task_id"
          class="mb-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
          :class="{ 'border-blue-400 bg-blue-50': currentTask?.task_id === t.task_id }"
          @click="selectTask(t.task_id)"
        >
          <div class="text-sm font-medium truncate">{{ t.goal }}</div>
          <div class="mt-1">
            <el-tag :type="t.status === 'SUCCESS' ? 'success' : t.status === 'FAILED' ? 'danger' : 'info'" size="small">
              {{ t.status }}
            </el-tag>
            <span class="ml-2 text-xs text-gray-400">{{ t.task_id }}</span>
          </div>
        </div>
      </div>

      <!-- 任务详情 -->
      <div class="w-2/3" v-loading="loadingDetail">
        <div v-if="!currentTask" class="text-gray-400">
          选择一个任务查看详情
        </div>
        <div v-else>
          <h2 class="text-lg font-semibold mb-2">{{ currentTask.goal }}</h2>
          <el-tag :type="currentTask.status === 'SUCCESS' ? 'success' : currentTask.status === 'FAILED' ? 'danger' : 'info'" class="mb-4">
            {{ currentTask.status }}
          </el-tag>

          <!-- 计划步骤 -->
          <h3 class="font-semibold mt-4 mb-2">执行步骤</h3>
          <div v-for="(s, i) in currentTask.steps" :key="s.step_id" class="flex items-center mb-2">
            <span class="w-6 h-6 rounded-full bg-gray-200 text-center text-sm leading-6 mr-2">{{ i + 1 }}</span>
            <span class="text-sm font-medium mr-2">{{ s.skill_name }}</span>
            <el-tag :type="statusType(s.status)" size="small">{{ s.status }}</el-tag>
            <span v-if="s.duration_ms != null" class="ml-2 text-xs text-gray-400">{{ (s.duration_ms / 1000).toFixed(2) }}s</span>
            <span v-if="s.error" class="ml-2 text-xs text-red-500">{{ s.error }}</span>
          </div>

          <!-- 交付物 -->
          <h3 class="font-semibold mt-6 mb-2">交付物（{{ currentTask.artifacts.length }}）</h3>
          <ArtifactPanel
            v-for="a in currentTask.artifacts"
            :key="a.artifact_id"
            :artifact="a"
            class="mb-2"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
