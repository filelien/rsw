'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tasksApi } from '@/lib/api'
import { CheckSquare, Plus, Play, Clock, X, Terminal, CheckCircle, XCircle, Loader } from 'lucide-react'

const STATUS_ICON: Record<string, any> = {
  success: <CheckCircle size={14} className="text-green-400" />,
  failed: <XCircle size={14} className="text-red-400" />,
  running: <Loader size={14} className="text-blue-400 animate-spin" />,
  pending: <Clock size={14} className="text-gray-400" />,
  timeout: <XCircle size={14} className="text-orange-400" />,
}

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"

export default function TasksPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState(false)
  const [selectedExec, setSelectedExec] = useState<any>(null)
  const [form, setForm] = useState({ name: '', description: '', script: '', script_type: 'bash', timeout_sec: 300 })

  const { data: tasks = [] } = useQuery({ queryKey: ['tasks'], queryFn: tasksApi.list })
  const { data: executions = [] } = useQuery({ queryKey: ['executions'], queryFn: () => tasksApi.listExecutions({ limit: 30 }), refetchInterval: 5000 })

  const createTask = useMutation({ mutationFn: tasksApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tasks'] }); setModal(false) } })
  const execTask = useMutation({ mutationFn: (id: string) => tasksApi.execute(id), onSuccess: () => qc.invalidateQueries({ queryKey: ['executions'] }) })
  const deleteTask = useMutation({ mutationFn: tasksApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['tasks'] }) })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><CheckSquare size={22} className="text-blue-400" /> Tâches & Automation</h1>
          <p className="text-gray-400 text-sm mt-1">Scripts, exécutions et planification</p>
        </div>
        <button onClick={() => setModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium">
          <Plus size={16} /> Nouvelle tâche
        </button>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Tasks list */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300">Tâches ({tasks.length})</h3>
          </div>
          <div className="divide-y divide-gray-800">
            {tasks.map((task: any) => (
              <div key={task.id} className="px-4 py-3 flex items-center justify-between hover:bg-gray-800/50">
                <div>
                  <p className="text-sm text-white font-medium">{task.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">{task.script_type}</span>
                    <span className="text-xs text-gray-600">{task.timeout_sec}s timeout</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => execTask.mutate(task.id)} className="flex items-center gap-1 text-xs bg-green-500/20 text-green-400 hover:bg-green-500/30 px-2 py-1 rounded">
                    <Play size={12} /> Exécuter
                  </button>
                  <button onClick={() => deleteTask.mutate(task.id)} className="text-gray-600 hover:text-red-400 text-xs px-1">✕</button>
                </div>
              </div>
            ))}
            {tasks.length === 0 && <p className="text-center py-10 text-gray-600 text-sm">Aucune tâche créée</p>}
          </div>
        </div>

        {/* Executions */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300">Exécutions récentes</h3>
          </div>
          <div className="divide-y divide-gray-800 max-h-96 overflow-y-auto">
            {executions.map((exec: any) => (
              <div key={exec.id} className="px-4 py-3 cursor-pointer hover:bg-gray-800/50" onClick={() => setSelectedExec(exec)}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {STATUS_ICON[exec.status] || <Clock size={14} className="text-gray-500" />}
                    <span className="text-sm text-white">{exec.task_id?.slice(0, 8)}...</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{exec.trigger_type}</p>
                    {exec.duration_ms && <p className="text-xs text-gray-600">{(exec.duration_ms/1000).toFixed(1)}s</p>}
                  </div>
                </div>
                <p className="text-xs text-gray-600 mt-1">{exec.created_at?.slice(0, 16)}</p>
              </div>
            ))}
            {executions.length === 0 && <p className="text-center py-10 text-gray-600 text-sm">Aucune exécution</p>}
          </div>
        </div>
      </div>

      {/* Create modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(false)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">Nouvelle Tâche</h2>
              <button onClick={() => setModal(false)} className="text-gray-500 hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div><label className="block text-xs text-gray-400 mb-1">Nom *</label>
                  <input className={inp} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="backup-database" /></div>
                <div><label className="block text-xs text-gray-400 mb-1">Type</label>
                  <select className={inp} value={form.script_type} onChange={e => setForm({ ...form, script_type: e.target.value })}>
                    {['bash','python','ansible'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select></div>
              </div>
              <div><label className="block text-xs text-gray-400 mb-1">Description</label>
                <input className={inp} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1 flex items-center gap-1"><Terminal size={12} /> Script *</label>
                <textarea className={`${inp} font-mono text-xs`} rows={8} value={form.script}
                  onChange={e => setForm({ ...form, script: e.target.value })}
                  placeholder="#!/bin/bash&#10;echo 'Hello from RAXUS'&#10;# Your script here" /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Timeout (secondes)</label>
                <input type="number" className={inp} value={form.timeout_sec} onChange={e => setForm({ ...form, timeout_sec: parseInt(e.target.value) })} /></div>
              <button onClick={() => createTask.mutate(form)} disabled={!form.name || !form.script}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer la tâche</button>
            </div>
          </div>
        </div>
      )}

      {/* Execution detail */}
      {selectedExec && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end" onClick={() => setSelectedExec(null)}>
          <div className="w-full max-w-2xl bg-gray-900 border-l border-gray-700 h-full overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">{STATUS_ICON[selectedExec.status]} Exécution</h2>
              <button onClick={() => setSelectedExec(null)} className="text-gray-500 hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Statut: </span><span className="text-white">{selectedExec.status}</span></div>
                <div><span className="text-gray-500">Durée: </span><span className="text-white">{selectedExec.duration_ms ? `${(selectedExec.duration_ms/1000).toFixed(2)}s` : '—'}</span></div>
                <div><span className="text-gray-500">Exit code: </span><span className="text-white">{selectedExec.exit_code ?? '—'}</span></div>
                <div><span className="text-gray-500">Trigger: </span><span className="text-white">{selectedExec.trigger_type}</span></div>
              </div>
              {selectedExec.output && (
                <div>
                  <label className="text-xs text-gray-400 mb-2 block">Sortie stdout</label>
                  <pre className="bg-gray-950 border border-gray-800 rounded-lg p-3 text-xs text-green-400 overflow-auto max-h-64 whitespace-pre-wrap">{selectedExec.output}</pre>
                </div>
              )}
              {selectedExec.error_output && (
                <div>
                  <label className="text-xs text-gray-400 mb-2 block">Sortie stderr</label>
                  <pre className="bg-gray-950 border border-gray-800 rounded-lg p-3 text-xs text-red-400 overflow-auto max-h-32 whitespace-pre-wrap">{selectedExec.error_output}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
