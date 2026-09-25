import { computed, reactive } from 'vue'
import { defineStore } from 'pinia'
import type { Message } from './messageList'

export type ChatDocumentSnapshot = {
  documentID?: string
  documentName: string
}

export type ChatSession = {
  id: string
  title: string
  updatedAt: number
  model: string
  modelLabel: string
  memory: string
  documents: ChatDocumentSnapshot[]
  messages: Message[]
}

function getStorageKey() {
  const username = localStorage.getItem('username') || 'guest'
  return `paperquery:chat-history:${username}`
}

function createSessionId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

export const useChatHistoryStore = defineStore('chatHistory', () => {
  const state = reactive({
    sessions: <ChatSession[]>[],
    currentSessionId: '',
  })

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(getStorageKey())
      state.sessions = raw ? JSON.parse(raw) : []
    } catch (error) {
      console.error('Load chat history failed:', error)
      state.sessions = []
    }
  }

  function persist() {
    localStorage.setItem(getStorageKey(), JSON.stringify(state.sessions))
  }

  function saveSnapshot(snapshot: Omit<ChatSession, 'id' | 'updatedAt'>) {
    if (snapshot.messages.length === 0) return

    if (!state.currentSessionId) {
      state.currentSessionId = createSessionId()
    }

    const session: ChatSession = {
      ...snapshot,
      id: state.currentSessionId,
      updatedAt: Date.now(),
    }
    const index = state.sessions.findIndex(item => item.id === session.id)
    if (index >= 0) {
      state.sessions[index] = session
    } else {
      state.sessions.unshift(session)
    }
    state.sessions.sort((a, b) => b.updatedAt - a.updatedAt)
    state.sessions = state.sessions.slice(0, 30)
    persist()
  }

  function startNewSession() {
    state.currentSessionId = createSessionId()
  }

  function useSession(sessionId: string) {
    state.currentSessionId = sessionId
  }

  function removeSession(sessionId: string) {
    state.sessions = state.sessions.filter(item => item.id !== sessionId)
    if (state.currentSessionId === sessionId) {
      state.currentSessionId = ''
    }
    persist()
  }

  const sessionList = computed(() => state.sessions)

  loadFromStorage()

  return {
    state,
    sessionList,
    loadFromStorage,
    saveSnapshot,
    startNewSession,
    useSession,
    removeSession,
  }
})
