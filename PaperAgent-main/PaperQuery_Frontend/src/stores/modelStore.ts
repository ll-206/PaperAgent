import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ModelType = 'deepseek' | 'kimi' | 'openai'

export const useModelStore = defineStore('model', () => {
  const currentModel = ref<ModelType>('deepseek')

  const modelOptions = [
    { value: 'deepseek', label: 'DeepSeek' },
    { value: 'kimi', label: 'Kimi K3' },
    { value: 'openai', label: 'OpenAI' },
  ]

  function setModel(model: ModelType) {
    currentModel.value = model
  }

  function getModelLabel(model: ModelType | string) {
    const option = modelOptions.find(item => item.value === model)
    return option?.label || 'DeepSeek'
  }

  return { currentModel, modelOptions, setModel, getModelLabel }
})
