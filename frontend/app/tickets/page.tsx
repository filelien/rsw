'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ticketsApi } from '@/lib/api'
import { Ticket, Plus, X } from 'lucide-react'

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
const PRIO: Record<string, string> = { critical: 'text-red-400 bg-red-500/10', high: 'text-orange-400 bg-orange-500/10', medium: 'text-yellow-400 bg-yellow-500/10', low: 'text-blue-400 bg-blue-500/10' }
const STAT: Record<string, string> = { open: 'text-red-300 bg-red-500/10', in_progress: 'text-blue-300 bg-blue-500/10', resolved: 'text-green-300 bg-green-500/10', closed: 'text-gray-400 bg-gray-500/10' }

export default function TicketsPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState(false)
  const [selected, setSelected] = useState<any>(null)
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium' })
  const [statusFilter, setStatusFilter] = useState('')

  const { data: tickets = [] } = useQuery({ queryKey: ['tickets', statusFilter], queryFn: () => ticketsApi.list({ status: statusFilter }) })
  const create = useMutation({ mutationFn: ticketsApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['tickets'] }); setModal(false) } })
  const update = useMutation({ mutationFn: ({ id, data }: any) => ticketsApi.update(id, data), onSuccess: () => qc.invalidateQueries({ queryKey: ['tickets'] }) })

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Ticket size={22} className="text-blue-400" /> Tickets</h1>
          <p className="text-gray-400 text-sm mt-1">Suivi des incidents et demandes</p>
        </div>
        <button onClick={() => setModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"><Plus size={16} /> Nouveau ticket</button>
      </div>

      <div className="flex gap-2">
        {['', 'open', 'in_progress', 'resolved', 'closed'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)} className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${statusFilter === s ? 'border-blue-500 bg-blue-500/20 text-blue-300' : 'border-gray-700 text-gray-400 hover:border-gray-600'}`}>
            {s || 'Tous'}
          </button>
        ))}
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
              <th className="text-left px-4 py-3">Titre</th>
              <th className="text-left px-4 py-3">Priorité</th>
              <th className="text-left px-4 py-3">Statut</th>
              <th className="text-left px-4 py-3">Créé</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((t: any) => (
              <tr key={t.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 cursor-pointer" onClick={() => setSelected(t)}>
                <td className="px-4 py-3"><p className="text-white truncate max-w-xs">{t.title}</p></td>
                <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded font-medium ${PRIO[t.priority]}`}>{t.priority}</span></td>
                <td className="px-4 py-3"><span className={`text-xs px-2 py-0.5 rounded font-medium ${STAT[t.status]}`}>{t.status}</span></td>
                <td className="px-4 py-3 text-gray-500 text-xs">{t.created_at?.slice(0, 10)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex gap-2 justify-end" onClick={e => e.stopPropagation()}>
                    {t.status === 'open' && <button onClick={() => update.mutate({ id: t.id, data: { status: 'in_progress' } })} className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Prendre</button>}
                    {t.status === 'in_progress' && <button onClick={() => update.mutate({ id: t.id, data: { status: 'resolved' } })} className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Résoudre</button>}
                  </div>
                </td>
              </tr>
            ))}
            {tickets.length === 0 && <tr><td colSpan={5} className="text-center py-12 text-gray-600">Aucun ticket</td></tr>}
          </tbody>
        </table>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(false)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5"><h2 className="text-lg font-bold text-white">Nouveau Ticket</h2><button onClick={() => setModal(false)}><X size={18} className="text-gray-500" /></button></div>
            <div className="space-y-4">
              <div><label className="block text-xs text-gray-400 mb-1">Titre *</label><input className={inp} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Priorité</label>
                <select className={inp} value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}>
                  {['critical','high','medium','low'].map(p => <option key={p} value={p}>{p}</option>)}
                </select></div>
              <div><label className="block text-xs text-gray-400 mb-1">Description</label><textarea className={inp} rows={4} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
              <button onClick={() => create.mutate(form)} disabled={!form.title} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer ticket</button>
            </div>
          </div>
        </div>
      )}

      {selected && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end" onClick={() => setSelected(null)}>
          <div className="w-full max-w-xl bg-gray-900 border-l border-gray-700 h-full overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-bold text-white">Ticket</h2><button onClick={() => setSelected(null)}><X size={18} className="text-gray-500" /></button></div>
            <div className="space-y-4">
              <p className="text-white font-semibold">{selected.title}</p>
              <div className="flex gap-2">
                <span className={`text-xs px-2 py-0.5 rounded ${PRIO[selected.priority]}`}>{selected.priority}</span>
                <span className={`text-xs px-2 py-0.5 rounded ${STAT[selected.status]}`}>{selected.status}</span>
              </div>
              {selected.description && <p className="text-gray-300 text-sm">{selected.description}</p>}
              <p className="text-xs text-gray-500">Créé: {selected.created_at}</p>
              <div className="flex gap-2 pt-4 border-t border-gray-800">
                {selected.status === 'open' && <button onClick={() => { update.mutate({ id: selected.id, data: { status: 'in_progress' } }); setSelected(null) }} className="flex-1 bg-blue-600 text-white py-2 rounded-lg text-sm">Prendre en charge</button>}
                {selected.status === 'in_progress' && <button onClick={() => { update.mutate({ id: selected.id, data: { status: 'resolved' } }); setSelected(null) }} className="flex-1 bg-green-600 text-white py-2 rounded-lg text-sm">Résoudre</button>}
                {(selected.status === 'resolved') && <button onClick={() => { update.mutate({ id: selected.id, data: { status: 'closed' } }); setSelected(null) }} className="flex-1 bg-gray-700 text-white py-2 rounded-lg text-sm">Fermer</button>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
