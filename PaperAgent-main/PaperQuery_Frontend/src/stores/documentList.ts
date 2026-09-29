import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'

export type Document = {
  isLoading: boolean
  documentID?: string
  documentName: string
  fileSize?: number
  documentFile?: File
  knowledgeID?: string
  source: 'library' | 'upload'
}

export const useDocumentListStore = defineStore('documentList', () => {
  const state = reactive({
    documentList: <Array<Document>>[],
  })

  const getDocumentList = computed(() => state.documentList)

  function appendDocument(document: Document) {
    if (
      document.documentID &&
      state.documentList.some(item => item.documentID === document.documentID)
    ) {
      return false
    }
    state.documentList.push(document)
    return true
  }

  function deleteDocument(index: number) {
    state.documentList.splice(index, 1)
  }

  // 按文档 ID 移除（用于知识库删除文档后，同步清理对话页绑定的残留文档）
  function deleteDocumentById(documentID: string) {
    const index = state.documentList.findIndex(item => item.documentID === documentID)
    if (index !== -1) {
      state.documentList.splice(index, 1)
      return true
    }
    return false
  }

  function getDocumentIDs() {
    return state.documentList
      .map(value => value.documentID)
      .filter((id): id is string => Boolean(id))
  }

  function getDocumentSnapshots() {
    return state.documentList.map((value) => {
      return {
        documentID: value.documentID?.toString(),
        documentName: value.documentName,
        knowledgeID: value.knowledgeID,
        source: value.source,
      }
    })
  }

  return {
    state,
    getDocumentIDs,
    getDocumentSnapshots,
    getDocumentList,
    appendDocument,
    deleteDocument,
    deleteDocumentById,
  }
})
