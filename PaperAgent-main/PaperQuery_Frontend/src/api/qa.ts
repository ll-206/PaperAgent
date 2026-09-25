import { consumeSSE } from './sse'

export interface CitationItem {
  id: string
  documentID: string
  knowledgeID?: string
  page: number
  chunk_id: string
}

// 走 V2 /qa/stream（带 citations），回调 delta 与 citations
export async function askQuestionStream(
  question: string,
  documentIds: string[],
  model: string,
  onDelta: (text: string) => void,
  onCitations: (citations: CitationItem[]) => void,
): Promise<void> {
  const token = localStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const res = await fetch(`${baseUrl}/qa/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      document_ids: documentIds,
      model,
      mode: 'ask',
    }),
  })
  if (!res.ok) {
    throw new Error(`请求失败：HTTP ${res.status}`)
  }
  await consumeSSE(res, (evt) => {
    if (evt.event === 'delta') {
      onDelta(evt.data?.text || '')
    } else if (evt.event === 'citations') {
      onCitations(evt.data?.items || [])
    }
  })
}
