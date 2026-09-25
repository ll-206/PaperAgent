<template>
  <div>
    <el-dropdown
      size="default"
      split-button
      type="default"
      trigger="click"
      :hide-on-click="true"
    >
      <p class="font-bold text-sm">{{ currentLabel }}</p>

      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item
            v-for="model in modelStore.modelOptions"
            :key="model.value"
            :class="{ 'text-blue-500 font-bold': model.value === modelStore.currentModel }"
            @click="handleSelect(model.value as ModelType)"
          >
            {{ model.label }}
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElNotification } from 'element-plus'
import { useModelStore, type ModelType } from '@/stores/modelStore'
import { useMessageListStore } from '@/stores/messageList'

const modelStore = useModelStore()
const messageListStore = useMessageListStore()

const currentLabel = computed(() => {
  const option = modelStore.modelOptions.find(m => m.value === modelStore.currentModel)
  return option ? option.label : 'DeepSeek'
})

function handleSelect(model: ModelType) {
  if (model === modelStore.currentModel) return

  const fromLabel = modelStore.getModelLabel(modelStore.currentModel)
  const toLabel = modelStore.getModelLabel(model)
  messageListStore.compressContextForModelSwitch(fromLabel, toLabel)
  modelStore.setModel(model)
  messageListStore.addSystemMessage(
    `已切换至 ${toLabel}。系统已压缩并保留当前上下文；切换模型无可避免可能导致回答准确率降低，请结合论文来源核对关键结论。`,
  )
  ElNotification({
    title: `已切换至 ${toLabel}`,
    message: '已压缩保留当前上下文。切换模型可能降低回答准确率，请注意核对。',
    type: 'warning',
    duration: 5000,
  })
}
</script>

<style scoped></style>
