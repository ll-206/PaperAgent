<script setup lang="ts">
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import '@tato30/vue-pdf/style.css'
import { useStore } from 'vuex'
import { translateText } from '@/api/data'
import Button from '@/components/ui/button/Button.vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const props = defineProps({
  knowledgeID: {
    type: String,
    required: true,
  },
  documentID: {
    type: String,
    required: true,
  },
})
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
const emit = defineEmits<{ selection: [text: string, page: number]; loaded: [] }>()
const route = useRoute()

// 手动 fetch 带鉴权头获取 PDF，避免 usePDF 直连 URL 因缺少 token 返回 401 导致左侧空白
const pdfUrl = ref<string | null>(null)
const { pdf, pages } = usePDF(pdfUrl)

async function loadPdf() {
  try {
    const token = localStorage.getItem('token')
    const resp = await fetch(
      `${apiBaseUrl}/document/getFile?documentID=${props.documentID}&knowledgeID=${props.knowledgeID}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} },
    )
    if (!resp.ok) throw new Error(`PDF 加载失败 (HTTP ${resp.status})`)
    const blob = await resp.blob()
    if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = URL.createObjectURL(blob)
  } catch (error: any) {
    ElMessage.error(error?.message || 'PDF 加载失败')
  }
}

const store = useStore()
const page = ref(1)
const container = ref<HTMLElement | null>(null)
const translating = ref(false)
let selectionVersion = 0

const jumpToPage = (target: number) => {
  const valid = Math.max(1, Math.min(target, pages.value || 1))
  page.value = valid
  container.value?.querySelector<HTMLElement>(`[data-pdf-page="${valid}"]`)?.scrollIntoView({ block: 'start' })
}

const updateCurrentPage = () => {
  if (!container.value) return
  const top = container.value.getBoundingClientRect().top
  const visible = [...container.value.querySelectorAll<HTMLElement>('[data-pdf-page]')]
    .find((element) => element.getBoundingClientRect().bottom > top + 40)
  if (visible) page.value = Number(visible.dataset.pdfPage)
}

const handleMouseUp = async () => {
  const selection = window.getSelection()
  const text = selection?.toString().trim() || ''
  if (!text || !container.value?.contains(selection?.anchorNode)) return
  const pageElement = (selection?.anchorNode instanceof Element
    ? selection.anchorNode : selection?.anchorNode?.parentElement)?.closest<HTMLElement>('[data-pdf-page]')
  const selectedPage = Number(pageElement?.dataset.pdfPage || page.value)
  emit('selection', text, selectedPage)
  store.commit('setSelectedText', text)
  store.commit('setTranslatedText', '正在使用本地模型翻译…')
  const version = ++selectionVersion
  translating.value = true
  try {
    const response = await translateText(text)
    if (version === selectionVersion) store.commit('setTranslatedText', response.data.text)
  } catch (error: any) {
    if (version === selectionVersion) store.commit('setTranslatedText', `翻译失败：${error?.message || '本地模型不可用'}`)
  } finally {
    translating.value = false
  }
}

onMounted(() => {
  loadPdf()
})

onBeforeUnmount(() => {
  selectionVersion++
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }
})

watch(pages, async (count) => {
  if (!count) return
  emit('loaded')
  await nextTick()
  jumpToPage(Number(route.query.page) || 1)
})
watch(() => route.query.page, async (value) => {
  if (!pages.value) return
  await nextTick()
  jumpToPage(Number(value) || 1)
})
</script>

<template>
  <div class="reader">
    <div class="reader-toolbar">
      <Button variant="ghost" :disabled="page <= 1" @click="jumpToPage(page - 1)">上一页</Button>
      <span>第 {{ page }} / {{ pages || '…' }} 页</span>
      <Button variant="ghost" :disabled="page >= pages" @click="jumpToPage(page + 1)">下一页</Button>
      <span class="reader-hint">在左侧连续滚动阅读；选中文字可离线翻译并用于提问</span>
    </div>
    <div ref="container" class="pdf-container" @scroll.passive="updateCurrentPage" @mouseup="handleMouseUp">
      <div v-for="pageNumber in pages" :key="pageNumber" :data-pdf-page="pageNumber" class="pdf-page">
        <VuePDF :pdf="pdf" :page="pageNumber" text-layer fit-parent />
        <span class="page-label">{{ pageNumber }} / {{ pages }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reader { display: flex; flex-direction: column; width: 100%; height: 100%; min-height: 0; }
.reader-toolbar { flex: none; display: flex; align-items: center; justify-content: center; gap: 12px; min-height: 44px; border-bottom: 1px solid #e5e7eb; background: #f9fafb; }
.reader-hint { margin-left: 16px; color: #6b7280; font-size: 12px; }
.pdf-container { flex: 1; min-height: 0; overflow: auto; padding: 16px 24px 32px; background: #e9edf3; scroll-behavior: smooth; }
.pdf-page { position: relative; width: min(100%, 1050px); margin: 0 auto 16px; background: white; box-shadow: 0 2px 10px #1f29371f; scroll-margin-top: 12px; }
.page-label { display: block; padding: 5px; text-align: center; color: #6b7280; font-size: 12px; }
</style>
