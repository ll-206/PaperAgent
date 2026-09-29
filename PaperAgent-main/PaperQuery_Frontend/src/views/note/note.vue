<template>
  <div class="note-panel">
    <div class="note-actions">
      <span class="save-status">{{ status }}</span>
      <button type="button" title="将剪贴板中的 Markdown 原文插入光标位置" @click="pasteMarkdown">粘贴 AI Markdown</button>
      <button type="button" title="导入本地 .md 文件并插入光标位置" @click="fileInput?.click()">导入 Markdown</button>
      <button type="button" :disabled="saving" @click="saveNote(true)">保存</button>
      <button type="button" @click="exportNote">导出 Markdown</button>
    </div>
    <input ref="fileInput" type="file" accept=".md,.markdown,text/markdown,text/plain" hidden @change="importMarkdown" />
    <p class="editor-hint">支持标题、大纲、表格、任务列表、代码块与数学公式；工具栏悬停可查看名称，右侧可切换编辑模式。</p>
    <div :id="editorId" class="note-editor"></div>
  </div>
</template>

<style scoped>
.note-panel { display: flex; flex-direction: column; height: 100%; min-height: 0; }
.note-actions { display: flex; align-items: center; gap: 8px; flex: none; flex-wrap: wrap; padding: 6px 0; }
.note-actions button { border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 8px; font-size: 12px; background: white; }
.note-actions button:hover { background: #eff6ff; }
.note-actions button:disabled { opacity: .5; }
.save-status { margin-right: auto; font-size: 12px; color: #64748b; }
.note-editor { flex: 1; min-height: 0; overflow: auto; }
.editor-hint { margin: 0 0 6px; color: #64748b; font-size: 11px; }
.note-editor :deep(.vditor-toolbar) { flex-wrap: wrap; gap: 2px; background: #f8f9fc; }
.note-editor :deep(.vditor-toolbar__item:hover) { background: #e8e4fb; border-radius: 5px; }
</style>

<script setup lang="ts">
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import { ElMessage } from 'element-plus'
import { getDocumentNote, updateDocumentNote } from '@/api/note'

const props = defineProps<{ knowledgeID: string; documentID: string }>()
const editorId = `paper-note-${props.documentID.replace(/[^a-zA-Z0-9_-]/g, '-')}`
const editor = ref<Vditor | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const status = ref('正在加载笔记…')
const saving = ref(false)
let saveTimer: ReturnType<typeof setTimeout> | undefined
let loading = true
let saveQueued = false

const saveNote = async (notify = false) => {
  if (!editor.value || loading) return
  if (saving.value) { saveQueued = true; return }
  clearTimeout(saveTimer)
  const content = editor.value.getValue()
  saving.value = true
  status.value = '保存中…'
  try {
    await updateDocumentNote(props.knowledgeID, props.documentID, content)
    status.value = `已保存 ${new Date().toLocaleTimeString()}`
    if (notify) ElMessage.success('笔记已保存')
  } catch (error: any) {
    status.value = '保存失败，请重试'
    ElMessage.error(error?.message || '笔记保存失败')
  } finally {
    saving.value = false
    if (saveQueued) { saveQueued = false; saveNote() }
  }
}

const onInput = () => {
  if (loading) return
  status.value = '未保存的修改'
  clearTimeout(saveTimer)
  saveTimer = setTimeout(() => saveNote(), 1000)
}

const exportNote = () => {
  const content = editor.value?.getValue() || ''
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `PaperAgent_笔记_${props.documentID}.md`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

const pasteMarkdown = async () => {
  try {
    const markdown = await navigator.clipboard.readText()
    if (!markdown.trim()) return ElMessage.info('剪贴板中没有文字')
    editor.value?.insertMD(markdown)
    onInput()
  } catch { ElMessage.warning('无法读取剪贴板，请在编辑区使用 Ctrl+V 粘贴') }
}

const importMarkdown = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) { ElMessage.warning('请选择小于 2 MB 的 Markdown 文件'); input.value = ''; return }
  editor.value?.insertMD(await file.text())
  input.value = ''
  onInput()
}

const onKeyDown = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault()
    saveNote(true)
  }
}

onMounted(() => {
  editor.value = new Vditor(editorId, {
    height: '100%', width: '100%', mode: 'ir',
    lang: 'zh_CN',
    toolbarConfig: { pin: true },
    counter: { enable: true, type: 'markdown' },
    toolbar: [
      { name: 'headings', tip: '标题' }, { name: 'bold', tip: '加粗' }, { name: 'italic', tip: '斜体' },
      { name: 'strike', tip: '删除线' }, '|', { name: 'list', tip: '无序列表' },
      { name: 'ordered-list', tip: '有序列表' }, { name: 'check', tip: '任务列表' },
      { name: 'quote', tip: '引用' }, { name: 'line', tip: '分隔线' }, '|',
      { name: 'code', tip: '代码块' }, { name: 'inline-code', tip: '行内代码' },
      { name: 'link', tip: '链接' }, { name: 'table', tip: '表格' }, '|',
      { name: 'undo', tip: '撤销' }, { name: 'redo', tip: '重做' },
      { name: 'outline', tip: '大纲' }, { name: 'edit-mode', tip: '切换编辑模式' },
      { name: 'fullscreen', tip: '全屏编辑' },
    ],
    cache: { enable: false },
    input: onInput,
    after: async () => {
      try {
        const response = await getDocumentNote(props.knowledgeID, props.documentID)
        editor.value?.setValue(response.data?.note || '# 我的笔记\n')
        status.value = '已加载，修改后自动保存'
      } catch (error: any) {
        editor.value?.setValue('# 我的笔记\n')
        status.value = '无法读取笔记，请检查文档状态'
      } finally { loading = false }
    },
  })
  window.addEventListener('keydown', onKeyDown)
})

onBeforeUnmount(() => {
  clearTimeout(saveTimer)
  if (status.value === '未保存的修改') saveNote()
  editor.value?.destroy()
  window.removeEventListener('keydown', onKeyDown)
})
</script>
