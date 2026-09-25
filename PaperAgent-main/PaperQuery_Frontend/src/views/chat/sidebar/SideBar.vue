<template>
  <aside class="h-full border-l border-gray-100 bg-[#f9f9f9]">
    <div class="flex items-center justify-between gap-2 border-b border-gray-100 p-4">
      <div>
        <div class="text-sm font-semibold text-gray-900">历史会话</div>
        <div class="text-xs text-gray-500">当前账号本地保存</div>
      </div>
      <el-button size="small" @click="startNewChat">新聊天</el-button>
    </div>

    <div class="h-[calc(100%-73px)] overflow-y-auto p-3">
      <el-empty
        v-if="sessions.length === 0"
        description="暂无历史记录"
        :image-size="72"
      />

      <button
        v-for="session in sessions"
        :key="session.id"
        class="mb-3 w-full rounded-md border border-gray-200 bg-white p-3 text-left transition hover:border-gray-300 hover:bg-gray-50"
        @click="restoreSession(session)"
      >
        <div class="truncate text-sm font-medium text-gray-900">
          {{ session.title }}
        </div>
        <div class="mt-1 flex items-center justify-between gap-2 text-xs text-gray-500">
          <span>{{ session.modelLabel }}</span>
          <span>{{ formatTime(session.updatedAt) }}</span>
        </div>
        <div class="mt-2 text-xs text-gray-500">
          {{ session.documents.length ? `绑定 ${session.documents.length} 篇论文` : '未绑定论文' }}
        </div>
        <div
          v-if="session.documents.length"
          class="mt-2 truncate text-xs text-gray-400"
          :title="session.documents.map(item => item.documentName).join(', ')"
        >
          {{ session.documents.map(item => item.documentName).join(', ') }}
        </div>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useChatHistoryStore, type ChatSession } from '@/stores/chatHistory'
import { useMessageListStore } from '@/stores/messageList'
import { useModelStore, type ModelType } from '@/stores/modelStore'

const historyStore = useChatHistoryStore()
const messageListStore = useMessageListStore()
const modelStore = useModelStore()
const sessions = computed(() => historyStore.sessionList)

function startNewChat() {
  messageListStore.clearMessages()
  ElMessage.success('已开启新聊天')
}

function restoreSession(session: ChatSession) {
  historyStore.useSession(session.id)
  modelStore.setModel(session.model as ModelType)
  messageListStore.restoreMessages(session.messages, session.memory)
  ElMessage.success('已恢复历史会话')
}

function formatTime(timestamp: number) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timestamp))
}
</script>
