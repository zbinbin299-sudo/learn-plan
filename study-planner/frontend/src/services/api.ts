import type { PlanRequest, StudyPlan, StudyTask, TaskStatus } from '../types'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? '请求失败，请确认后端服务已启动。')
  }
  return response.json() as Promise<T>
}

export function generatePlan(payload: PlanRequest): Promise<StudyPlan> {
  return request('/api/plans/generate', { method: 'POST', body: JSON.stringify(payload) })
}

export function getCurrentPlan(learnerId: string): Promise<StudyPlan | null> {
  return request(`/api/plans/current?learner_id=${encodeURIComponent(learnerId)}`)
}

export function updateTask(taskId: string, status: TaskStatus): Promise<StudyTask> {
  return request(`/api/tasks/${encodeURIComponent(taskId)}`, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  })
}