'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/lib/api'
import { Mail, Plus, X, Send, CheckCircle, XCircle } from 'lucide-react'

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
const TYPE_ICON: Record<string, string> = { email: '📧', webhook: '🔗', slack: '💬', teams: '🟦', pagerduty: '🚨', sms: '📱' }

export default function NotificationsPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState(false)
  const [form, setForm] = useState({ name: '', type: 'email', config: '{}' })
  const [testResult, setTestResult] = useState<Record<string, boolean>>({})

  const { data: notifiers = [] } = useQuery({ queryKey: ['notifiers'], queryFn: notificationsApi.list })
  const { data: history = [] } = useQuery({ queryKey: ['notifHistory'], queryFn: notificationsApi.getHistory })

  const create = useMutation({ mutationFn: (d: any) => notificationsApi.create({ ...d, config: JSON.parse(d.config) }), onSuccess: () => { qc.invalidateQueries({ queryKey: ['notifiers'] }); setModal(false) } })
  const remove = useMutation({ mutationFn: notificationsApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['notifiers'] }) })
  const test = useMutation({ mutationFn: notificationsApi.test, onSuccess: (data, id) => setTestResult(r => ({ ...r, [id]: data.success })) })

  const configTemplates: Record<string, string> = {
    email: '{"to": ["ops@company.com"]}',
    webhook: '{"url": "https://example.com/webhook", "headers": {"Authorization": "Bearer token"}}',
    slack: '{"webhook_url": "https://hooks.slack.com/services/xxx"}',
    teams: '{"webhook_url": "https://outlook.office.com/webhook/xxx"}',
    pagerduty: '{"integration_key": "your-key"}',
    sms: '{"phone": "+1234567890", "provider": "twilio"}',
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white flex items-center gap-2"><Mail size={22} className="text-blue-400" /> Notifications</h1>
          <p className="text-gray-400 text-sm mt-1">Canaux de notification et historique</p></div>
        <button onClick={() => setModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"><Plus size={16} /> Ajouter canal</button>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Notifiers */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-400">Canaux configurés</h3>
          {notifiers.map((n: any) => (
            <div key={n.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xl">{TYPE_ICON[n.type] || '📡'}</span>
                  <div>
                    <p className="font-medium text-white">{n.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{n.type}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {testResult[n.id] !== undefined && (
                    testResult[n.id] ? <CheckCircle size={14} className="text-green-400" /> : <XCircle size={14} className="text-red-400" />
                  )}
                  <button onClick={() => test.mutate(n.id)} className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-2 py-1 rounded flex items-center gap-1"><Send size={10} /> Test</button>
                  <button onClick={() => remove.mutate(n.id)} className="text-gray-600 hover:text-red-400">✕</button>
                </div>
              </div>
            </div>
          ))}
          {notifiers.length === 0 && <div className="text-center py-10 text-gray-600 bg-gray-900 border border-gray-800 rounded-xl text-sm">Aucun canal configuré</div>}
        </div>

        {/* History */}
        <div>
          <h3 className="text-sm font-medium text-gray-400 mb-3">Historique récent</h3>
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="divide-y divide-gray-800 max-h-80 overflow-y-auto">
              {history.slice(0, 20).map((h: any) => (
                <div key={h.id} className="px-4 py-2.5 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-300">{h.notifier_id?.slice(0, 8)}...</p>
                    <p className="text-xs text-gray-600">{h.created_at?.slice(0, 16)}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded ${h.status === 'sent' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{h.status}</span>
                </div>
              ))}
              {history.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">Aucun historique</p>}
            </div>
          </div>
        </div>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(false)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5"><h2 className="text-lg font-bold text-white">Nouveau canal</h2><button onClick={() => setModal(false)}><X size={18} className="text-gray-500" /></button></div>
            <div className="space-y-4">
              <div><label className="block text-xs text-gray-400 mb-1">Nom *</label><input className={inp} value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Type</label>
                <select className={inp} value={form.type} onChange={e => setForm({ ...form, type: e.target.value, config: configTemplates[e.target.value] || '{}' })}>
                  {Object.keys(TYPE_ICON).map(t => <option key={t} value={t}>{TYPE_ICON[t]} {t}</option>)}
                </select></div>
              <div><label className="block text-xs text-gray-400 mb-1">Configuration (JSON)</label>
                <textarea className={`${inp} font-mono text-xs`} rows={6} value={form.config} onChange={e => setForm({ ...form, config: e.target.value })} /></div>
              <button onClick={() => { try { create.mutate(form) } catch { alert('JSON invalide') } }} disabled={!form.name} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm">Créer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
