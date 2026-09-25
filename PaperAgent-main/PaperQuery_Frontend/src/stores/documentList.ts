import { defineStore } from 'pinia'
import { reactive, computed } from 'vue'

export type Document = {
  isLoading: boolean
  documentID?: String | undefined
  documentFile: File
}

export const useDocumentListStore = defineStore('documentList', () => {
  const state = reactive({
    documentList: <Array<Document>>[],
  })

  const getDocumentList = computed(() => state.documentList)

  function appendDocument(document: Document) {
    state.documentList.push(document)
  }

  function deleteDocument(index: number) {
    state.documentList.splice(index, 1)
  }

  function getDocumentIDs() {
    return state.documentList.map((value, _) => {
      return value.documentID
    })
  }

  function getDocumentSnapshots() {
    return state.documentList.map((value) => {
      return {
        documentID: value.documentID?.toString(),
        documentName: value.documentFile.name,
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
  }
})
