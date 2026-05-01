import axios from 'axios'
import { getSession } from 'next-auth/react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: `${API_URL}/api/v1` })

api.interceptors.request.use(async (config) => {
  const session = await getSession()
  if (session?.accessToken) {
    config.headers.Authorization = `Bearer ${session.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.location.href = '/auth/signin'
    }
    return Promise.reject(err)
  }
)

// ─── Dashboard ───────────────────────────────────────────────────
export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary').then(r => r.data),
  getTimeline: (days = 7) => api.get(`/dashboard/timeline?days=${days}`).then(r => r.data),
  getTopIssues: () => api.get('/dashboard/top-issues').then(r => r.data),
}

// ─── Alerts ──────────────────────────────────────────────────────
export const alertsApi = {
  list: (params?: any) => api.get('/alerts', { params }).then(r => r.data),
  get: (id: string) => api.get(`/alerts/${id}`).then(r => r.data),
  acknowledge: (id: string, note?: string) => api.post(`/alerts/${id}/acknowledge`, { note }).then(r => r.data),
  resolve: (id: string) => api.post(`/alerts/${id}/resolve`).then(r => r.data),
  getStats: () => api.get('/alerts/stats').then(r => r.data),
  getHistory: (days = 7) => api.get(`/alerts/history?days=${days}`).then(r => r.data),
  createSuppression: (data: any) => api.post('/alerts/suppression', data).then(r => r.data),
  listSuppressions: () => api.get('/alerts/suppression').then(r => r.data),
}

// ─── Inventory ───────────────────────────────────────────────────
export const inventoryApi = {
  listDatacenters: () => api.get('/inventory/datacenters').then(r => r.data),
  createDatacenter: (data: any) => api.post('/inventory/datacenters', data).then(r => r.data),
  updateDatacenter: (id: string, data: any) => api.patch(`/inventory/datacenters/${id}`, data).then(r => r.data),
  deleteDatacenter: (id: string) => api.delete(`/inventory/datacenters/${id}`).then(r => r.data),
  listEnvironments: (dcId?: string) => api.get('/inventory/environments', { params: { datacenter_id: dcId } }).then(r => r.data),
  createEnvironment: (data: any) => api.post('/inventory/environments', data).then(r => r.data),
  listServers: (params?: any) => api.get('/inventory/servers', { params }).then(r => r.data),
  getServer: (id: string) => api.get(`/inventory/servers/${id}`).then(r => r.data),
  createServer: (data: any) => api.post('/inventory/servers', data).then(r => r.data),
  updateServer: (id: string, data: any) => api.patch(`/inventory/servers/${id}`, data).then(r => r.data),
  deleteServer: (id: string) => api.delete(`/inventory/servers/${id}`).then(r => r.data),
  listComponents: (serverId?: string) => api.get('/inventory/components', { params: { server_id: serverId } }).then(r => r.data),
  createComponent: (data: any) => api.post('/inventory/components', data).then(r => r.data),
  getStats: () => api.get('/inventory/stats').then(r => r.data),
}

// ─── Tasks ───────────────────────────────────────────────────────
export const tasksApi = {
  list: () => api.get('/tasks').then(r => r.data),
  get: (id: string) => api.get(`/tasks/${id}`).then(r => r.data),
  create: (data: any) => api.post('/tasks', data).then(r => r.data),
  update: (id: string, data: any) => api.patch(`/tasks/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/tasks/${id}`).then(r => r.data),
  execute: (id: string, data?: any) => api.post(`/tasks/${id}/execute`, data || {}).then(r => r.data),
  listExecutions: (params?: any) => api.get('/tasks/executions', { params }).then(r => r.data),
  listSchedules: () => api.get('/tasks/schedules').then(r => r.data),
  createSchedule: (data: any) => api.post('/tasks/schedules', data).then(r => r.data),
}

// ─── SLO ─────────────────────────────────────────────────────────
export const sloApi = {
  list: () => api.get('/slo').then(r => r.data),
  get: (id: string) => api.get(`/slo/${id}`).then(r => r.data),
  create: (data: any) => api.post('/slo', data).then(r => r.data),
  update: (id: string, data: any) => api.patch(`/slo/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/slo/${id}`).then(r => r.data),
  listProbes: () => api.get('/slo/probes').then(r => r.data),
  createProbe: (data: any) => api.post('/slo/probes', data).then(r => r.data),
  getStats: () => api.get('/slo/stats').then(r => r.data),
}

// ─── Notifications ───────────────────────────────────────────────
export const notificationsApi = {
  list: () => api.get('/notifications').then(r => r.data),
  create: (data: any) => api.post('/notifications', data).then(r => r.data),
  update: (id: string, data: any) => api.patch(`/notifications/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/notifications/${id}`).then(r => r.data),
  test: (id: string) => api.post(`/notifications/${id}/test`).then(r => r.data),
  getHistory: () => api.get('/notifications/history').then(r => r.data),
}

// ─── Rules ───────────────────────────────────────────────────────
export const rulesApi = {
  list: () => api.get('/rules').then(r => r.data),
  get: (id: string) => api.get(`/rules/${id}`).then(r => r.data),
  create: (data: any) => api.post('/rules', data).then(r => r.data),
  update: (id: string, data: any) => api.patch(`/rules/${id}`, data).then(r => r.data),
  delete: (id: string) => api.delete(`/rules/${id}`).then(r => r.data),
  test: (id: string, data: any) => api.post(`/rules/${id}/test`, data).then(r => r.data),
}

// ─── Tickets ─────────────────────────────────────────────────────
export const ticketsApi = {
  list: (params?: any) => api.get('/tickets', { params }).then(r => r.data),
  get: (id: string) => api.get(`/tickets/${id}`).then(r => r.data),
  create: (data: any) => api.post('/tickets', data).then(r => r.data),
  update: (id: string, data: any) => api.patch(`/tickets/${id}`, data).then(r => r.data),
  addComment: (id: string, data: any) => api.post(`/tickets/${id}/comments`, data).then(r => r.data),
}

// ─── Auth ────────────────────────────────────────────────────────
export const authApi = {
  me: () => api.get('/auth/me').then(r => r.data),
  listApiKeys: () => api.get('/auth/api-keys').then(r => r.data),
  createApiKey: (name: string) => api.post(`/auth/api-keys?name=${name}`).then(r => r.data),
  revokeApiKey: (id: string) => api.delete(`/auth/api-keys/${id}`).then(r => r.data),
}

export default api
