<template>
  <div v-if="props.role === 'system'" class="flex justify-center">
    <div class="max-w-[72%] rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-700">
      {{ props.content }}
    </div>
  </div>

  <div v-else-if="props.role === 'gpt'" class="flex justify-start">
    <el-card shadow="hover" class="card rounded-3xl">
      <div
        v-if="props.modelLabel"
        class="mb-2 text-xs font-medium text-gray-500"
      >
        {{ props.modelLabel }}
      </div>
      <div v-if="props.status === 'thinking' && !props.content" class="thinking-state" role="status">
        <span>正在思考</span>
        <span class="thinking-dots" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
      </div>
      <div v-else class="render" v-html="renderContent(props.content)" @click="handleCitationClick" />
    </el-card>
  </div>

  <div v-else class="flex justify-end">
    <el-card shadow="hover" class="back-color card rounded-3xl">
      <div class="render" v-html="renderMarkdown(props.content)" />
    </el-card>
  </div>
</template>

<style lang="less" scoped>
@import '@/styles/markdown-styles-light.less';

.back-color {
  background-color: #f4f4f4;
}

:deep(.card) .el-card__body {
  padding: 14px 16px !important;
}

:deep(.card) { border: 1px solid #e8e8ea; border-radius: 16px !important; box-shadow: none !important; transition: border-color .18s ease, background .18s ease; }
:deep(.card:hover) { border-color: #dddde1; }
.back-color { border-color: transparent !important; background: #f3f3f4; }

.thinking-state {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 24px;
  color: #6b7280;
  font-size: 14px;
}

.thinking-dots {
  display: inline-flex;
  gap: 3px;
}

.thinking-dots i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #7767c5;
  animation: thinking-pulse 1.2s ease-in-out infinite;
}

.thinking-dots i:nth-child(2) {
  animation-delay: 0.15s;
}

.thinking-dots i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes thinking-pulse {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-2px); }
}
</style>

<script setup lang="ts">
import { ElCard } from 'element-plus'
import { useRouter } from 'vue-router'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'
import type { CitationItem } from '@/api/qa'

const props = defineProps<{
  role: string
  content: string
  modelLabel?: string
  citations?: CitationItem[]
  status?: 'thinking' | 'streaming' | 'done' | 'error'
}>()

const router = useRouter()

const highlightCode = (str: string, lang: string): string => {
  const language = hljs.getLanguage(lang)
  if (language) {
    try {
      return (
        '<pre class="hljs"><code>' +
        hljs.highlight(lang, str, true).value +
        '</code></pre>'
      )
    } catch (error) {
      console.error(error)
    }
  }
  return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
}

const md = new MarkdownIt({
  breaks: true,
  html: true,
  linkify: true,
  typographer: true,
  highlight: highlightCode,
})

const renderMarkdown = (text: string) => {
  return md.render(text)
}

// 把 [C#] 引用替换为可点击链接（携带 knowledgeID/documentID/page）
const renderContent = (text: string) => {
  let processed = text
  if (props.citations?.length) {
    processed = text.replace(/\[(C\d+)\]/g, (match, cid) => {
      const c = props.citations!.find((x) => x.id === cid)
      if (!c) return match
      return `<a class="citation-link" data-kid="${c.knowledgeID || ''}" data-doc="${c.documentID}" data-page="${c.page}">${match}</a>`
    })
  }
  return md.render(processed)
}

const handleCitationClick = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.classList.contains('citation-link')) return
  const kid = target.dataset.kid
  const doc = target.dataset.doc
  const page = target.dataset.page
  if (kid && doc) {
    router.push({
      name: 'pdfInfo',
      params: { knowledgeID: kid, documentID: doc },
      query: { page },
    })
  }
}
</script>
