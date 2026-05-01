// rules/page.tsx
'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rulesApi } from '@/lib/api'
import { GitBranch, Plus, X, Play } from 'lucide-react'

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"

export default function RulesPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState(false)
  const [form, setForm] = useState<any>({ name: '', description: '', priority: 100, conditions: { match: 'all', rules: [{ field: 'severity', operator: 'eq', value: 'critical' }] }, actions: { list: [] } })

  const { data: rules = [] } = useQuery({ queryKey: ['rules'], queryFn: rulesApi.list })
  const create = useMutation({ mutationFn: rulesApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['rules'] }); setModal(false) } })
  const update = useMutation({ mutationFn: ({ id, data }: any) => rulesApi.update(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }) })
  const remove = useMutation({ mutationFn: rulesApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['rules'] }) })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><GitBranch size={22} className="text-blue-400" /> Règles</h1>
          <p className="text-gray-400 text-sm mt-1">Automatisation basée sur les conditions d'alertes</p></div>
        <button onClick={() => setModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"><Plus size={16} /> Nouvelle règle</button>
      </div>
      <div className="grid gap-3">
        {rules.map((rule: any) => (
          <div key={rule.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium text-white">{rule.name}</h3>
                  <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">Priority {rule.priority}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${rule.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>{rule.is_active ? 'Active' : 'Inactive'}</span>
                </div>
                {rule.description && <p className="text-xs text-gray-500 mt-1">{rule.description}</p>}
                <div className="mt-2 flex gap-4 text-xs text-gray-500">
                  <span>Conditions: {rule.conditions?.rules?.length || 0}</span>
                  <span>Actions: {rule.actions?.list?.length || 0}</span>
                  <span>Déclenchements: {rule.trigger_count || 0}</span>
                  {rule.last_triggered && <span>Dernier: {rule.last_triggered.slice(0, 16)}</span>}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => update.mutate({ id: rule.id, data: { is_active: !rule.is_active } })} className={`text-xs px-2 py-1 rounded ${rule.is_active ? 'bg-gray-700 text-gray-300' : 'bg-green-600 text-white'}`}>
                  {rule.is_active ? 'Désactiver' : 'Activer'}
                </button>
                <button onClick={() => remove.mutate(rule.id)} className="text-gray-600 hover:text-red-400">✕</button>
              </div>
            </div>
          </div>
        ))}
        {rules.length === 0 && <div className="text-center py-16 text-gray-600 bg-gray-900 border border-gray-800 rounded-xl">Aucune règle configurée</div>}
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(false)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5"><h2 className="text-lg font-bold text-white">Nouvelle Règle</h2><button onClick={() => setModal(false)}><X size={18} className="text-gray-500" /></button></div>
            <div className="space-y-4">
              <div><label className="block text-xs text-gray-400 mb-1">Nom *</label><input className={inp} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Description</label><input className={inp} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Priorité</label><input type="number" className={inp} value={form.priority} onChange={e => setForm({ ...form, priority: parseInt(e.target.value) })} /></div>
              <div className="bg-gray-800 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-2">Condition par défaut</p>
                <code className="text-xs text-green-400">severity == critical</code>
              </div>
              <p className="text-xs text-gray-500">Les conditions et actions peuvent être configurées via l'API ou le fichier YAML.</p>
              <button onClick={() => create.mutate(form)} disabled={!form.name} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm">Créer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
