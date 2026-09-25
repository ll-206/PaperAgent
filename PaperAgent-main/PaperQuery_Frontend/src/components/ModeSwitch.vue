<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import {
  useWorkspaceModeStore,
  type WorkspaceMode,
} from '@/stores/workspaceMode'

const router = useRouter()
const store = useWorkspaceModeStore()

const modes: Array<{ value: WorkspaceMode; label: string }> = [
  { value: 'ask', label: 'Ask' },
  { value: 'research', label: 'Research' },
  { value: 'experiment', label: 'Experiment' },
]

const switchMode = (m: WorkspaceMode) => {
  store.setMode(m)
  if (m === 'research') {
    router.push('/home/research')
  } else if (m === 'ask') {
    router.push('/home/Chat')
  } else {
    ElNotification.info({ title: 'Experiment', message: 'Experiment 模式暂未实现' })
  }
}
</script>

<template>
  <div class="flex items-center space-x-1 rounded-lg bg-gray-100 p-1">
    <button
      v-for="m in modes"
      :key="m.value"
      type="button"
      class="rounded-md px-3 py-1 text-sm font-medium transition-colors"
      :class="
        store.mode === m.value
          ? 'bg-white text-gray-900 shadow-sm'
          : 'text-gray-500 hover:text-gray-700'
      "
      @click="switchMode(m.value)"
    >
      {{ m.label }}
    </button>
  </div>
</template>
