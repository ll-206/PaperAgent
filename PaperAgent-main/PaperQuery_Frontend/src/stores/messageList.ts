import { computed, reactive } from 'vue'
import { defineStore } from 'pinia'
import { updateMemory } from '@/api/chat'
import { askQuestionStream, type CitationItem } from '@/api/qa'
import { useChatHistoryStore } from './chatHistory'
import { useDocumentListStore } from './documentList'
import { useMemoryStore } from './memory'
import { useModelStore } from './modelStore'

export type Message = {
  id?: number
  content: string
  role: 'user' | 'gpt' | 'system'
  model?: string
  modelLabel?: string
  createdAt?: number
  citations?: CitationItem[]
}

export const useMessageListStore = defineStore('messageList', () => {
  const state = reactive({
    messageList: <Array<Message>>[],
  })

  const messages = computed(() => state.messageList)

  function addUserMessage(message: Message) {
    const userMessage: Message = {
      ...message,
      id: state.messageList.length,
      createdAt: Date.now(),
    }
    state.messageList.push(userMessage)
    saveHistorySnapshot()
    addGptMessage(userMessage.content)
  }

  function addSystemMessage(content: string) {
    state.messageList.push({
      id: state.messageList.length,
      content,
      role: 'system',
      createdAt: Date.now(),
    })
    saveHistorySnapshot()
  }

  function addGptMessage(question: string) {
    const modelStore = useModelStore()
    const model = modelStore.currentModel
    const modelLabel = modelStore.getModelLabel(model)
    const newId = state.messageList.length
    const ids = useDocumentListStore().getDocumentIDs() as Array<string>
    const memory = useMemoryStore().getMemory
    let answer = ''
    let citations: CitationItem[] = []

    function updateMessage(id: number, content: string) {
      if (!state.messageList[id]) {
        state.messageList.push({
          id,
          content,
          role: 'gpt',
          model,
          modelLabel,
          createdAt: Date.now(),
        })
      } else {
        state.messageList[id].content += content
      }
    }

    askQuestionStream(
      question,
      ids,
      model,
      (text) => {
        answer += text
        updateMessage(newId, text)
      },
      (cits) => {
        citations = cits
      },
    )
      .then(() => {
        if (state.messageList[newId]) {
          state.messageList[newId].citations = citations
        }
        return updateMemory(question, memory, answer)
      })
      .then((data: any) => {
        if (data?.context) {
          useMemoryStore().setMemory(data.context)
        }
        saveHistorySnapshot()
      })
      .catch((error) => {
        console.error(error)
        addSystemMessage(`模型调用失败：${error?.message || error}`)
      })
  }

  function compressContextForModelSwitch(fromModel: string, toModel: string) {
    const recentMessages = state.messageList
      .filter(message => message.role !== 'system' && message.content.trim())
      .slice(-8)
      .map((message) => {
        const role = message.role === 'user' ? '用户' : '助手'
        return `${role}: ${message.content.trim()}`
      })
      .join('\n')
    const documents = useDocumentListStore().getDocumentSnapshots()
    const documentText = documents.length
      ? documents.map(item => item.documentName).join(', ')
      : '当前未绑定论文'

    const compressed = [
      `模型已从 ${fromModel} 切换为 ${toModel}。`,
      '以下是为降低跨模型上下文漂移而压缩后的对话记忆：',
      `当前论文上下文：${documentText}`,
      recentMessages || '暂无历史对话。',
    ].join('\n')

    useMemoryStore().setMemory(compressed.slice(-3000))
    saveHistorySnapshot()
  }

  function clearMessages() {
    state.messageList = []
    useMemoryStore().clearMemory()
    useChatHistoryStore().startNewSession()
  }

  function restoreMessages(messagesToRestore: Message[], memory = '') {
    state.messageList = messagesToRestore.map((message, index) => ({
      ...message,
      id: index,
    }))
    useMemoryStore().setMemory(memory)
  }

  function saveHistorySnapshot() {
    const firstUserMessage = state.messageList.find(message => message.role === 'user')
    const modelStore = useModelStore()
    useChatHistoryStore().saveSnapshot({
      title: firstUserMessage?.content.slice(0, 24) || '新聊天',
      model: modelStore.currentModel,
      modelLabel: modelStore.getModelLabel(modelStore.currentModel),
      memory: useMemoryStore().getMemory,
      documents: useDocumentListStore().getDocumentSnapshots(),
      messages: state.messageList,
    })
  }

  return {
    state,
    messages,
    addUserMessage,
    addSystemMessage,
    clearMessages,
    restoreMessages,
    compressContextForModelSwitch,
    saveHistorySnapshot,
  }
})
