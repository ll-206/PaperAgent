<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

interface ArtifactData {
  artifact_id: string
  type: string
  title: string
  data?: Record<string, any>
}

const props = defineProps<{ artifact: ArtifactData }>()

const highlightCode = (str: string, lang: string): string => {
  if (lang && hljs.getLanguage(lang)) {
    try {
      return (
        '<pre class="hljs"><code>' +
        hljs.highlight(lang, str, true).value +
        '</code></pre>'
      )
    } catch (e) {
      console.error(e)
    }
  }
  return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>'
}

const md = new MarkdownIt({
  breaks: true,
  html: true,
  linkify: true,
  highlight: highlightCode,
})

const markdown = computed(() => {
  const d = props.artifact.data || {}
  return d.markdown || d.report || ''
})

const tableData = computed<{ columns: string[]; rows: Array<Record<string, any>> } | null>(() => {
  const d = props.artifact.data || {}
  if (props.artifact.type === 'comparison_table') {
    if (d.columns && d.rows) {
      return { columns: d.columns, rows: d.rows }
    }
    // 尝试解析 raw JSON
    if (typeof d.raw === 'string') {
      try {
        const parsed = JSON.parse(d.raw)
        if (parsed.columns && parsed.rows) {
          return { columns: parsed.columns, rows: parsed.rows }
        }
      } catch {
        /* ignore */
      }
    }
  }
  return null
})

const rawText = computed(() => {
  const d = props.artifact.data || {}
  if (typeof d.raw === 'string') return d.raw
  return JSON.stringify(d, null, 2)
})
</script>

<template>
  <div class="rounded-lg border p-4">
    <div class="mb-2 flex items-center justify-between">
      <span class="text-sm font-medium">{{ artifact.title }}</span>
      <el-tag size="small">{{ artifact.type }}</el-tag>
    </div>

    <!-- Markdown 报告 -->
    <div
      v-if="artifact.type === 'research_report' && markdown"
      class="render"
      v-html="md.render(markdown)"
    />

    <!-- 对比表 -->
    <el-table v-else-if="tableData" :data="tableData.rows" border size="small" max-height="400">
      <el-table-column
        v-for="col in tableData.columns"
        :key="col"
        :prop="col"
        :label="col"
      />
    </el-table>

    <!-- 其他：展示原始文本 -->
    <pre v-else class="whitespace-pre-wrap text-sm text-gray-700">{{ rawText }}</pre>
  </div>
</template>

<style scoped>
:deep(.render) {
  font-size: 0.875rem;
  line-height: 1.6;
}
</style>
