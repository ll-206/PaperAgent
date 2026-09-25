import api from '@/api/api'

// 创建 Research 任务（可能耗时较长，覆盖默认 timeout）
export const createResearchTask = async (
  goal: string,
  mode = 'research',
  documentIds: string[] = [],
) => {
  const token = localStorage.getItem('token')
  const resp = await api.post(
    '/research/tasks',
    { goal, mode, document_ids: documentIds },
    {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 180000,
    },
  )
  return resp.data
}

// 任务列表
export const listResearchTasks = async () => {
  const token = localStorage.getItem('token')
  const resp = await api.get('/research/tasks', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return resp.data
}

// 任务详情
export const getResearchTask = async (taskId: string) => {
  const token = localStorage.getItem('token')
  const resp = await api.get(`/research/tasks/${taskId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  return resp.data
}
