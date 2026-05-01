'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { alertsApi } from '@/lib/api'
import { AlertTriangle, CheckCircle, Eye, Filter, Search, RefreshCw, Bell, X } from 'lucide-react'

const SEV_BADGE: Record<string, string> = {
  critical: 'bg-red-500/20 text-red-400 border border-red-500/30',
  major: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  minor: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  warning: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  info: 'bg-green-500/20 text-green-400 border border-green-500/30',
}
const STATUS_BADGE: Record<string, string> = {
  active: 'bg-red-500/20 text-red-300',
  acknowledged: 'bg-yellow-500/20 text-yellow-300',
  resolved: 'bg-green-500/20 text-green-300',
  suppressed: 'bg-gray-500/20 text-gray-300',
}

export default function AlertsPage() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [selected, setSelected] = useState<any>(null)

  const { data: alerts = [], isLoading, refetch } = useQuery({
    queryKey: ['alerts', search, statusFilter, severityFilter],
    queryFn: () => alertsApi.list({ search, status: statusFilter, severity: severityFilter }),
    refetchInterval: 15_000,
  })

  const { data: stats } = useQuery({ queryKey: ['alertStats'], queryFn: alertsApi.getStats })

  const ack = useMutation({
    mutationFn: (id: string) => alertsApi.acknowledge(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })
  const resolve = useMutation({
    mutationFn: (id: string) => alertsApi.resolve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Bell size={22} className="text-blue-400" /> Alertes
          </h1>
          <p className="text-gray-400 text-sm mt-1">Gestion centralisée des alertes</p>
        </div>
        <button onClick={() => refetch()} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white bg-gray-800 px-3 py-2 rounded-lg">
          <RefreshCw size={14} /> Actualiser
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-5 gap-3">
        {[
          { label: 'Actives', val: stats?.by_status?.active ?? 0, color: 'text-red-400' },
          { label: 'Acknowled.', val: stats?.by_status?.acknowledged ?? 0, color: 'text-yellow-400' },
          { label: 'Résolues', val: stats?.by_status?.resolved ?? 0, color: 'text-green-400' },
          { label: 'Critical', val: stats?.by_severity?.critical ?? 0, color: 'text-red-500' },
          { label: 'Total', val: stats?.total ?? 0, color: 'text-gray-300' },
        ].map(({ label, val, color }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-3 text-center">
            <p className={`text-xl font-bold ${color}`}>{val}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher alertes..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500" />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
          <option value="">Tous statuts</option>
          {['active','acknowledged','resolved','suppressed'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
          <option value="">Toutes sévérités</option>
          {['critical','major','minor','warning','info'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400 text-xs uppercase tracking-wide">
              <th className="text-left px-4 py-3">Nom</th>
              <th className="text-left px-4 py-3">Sévérité</th>
              <th className="text-left px-4 py-3">Statut</th>
              <th className="text-left px-4 py-3">Instance</th>
              <th className="text-left px-4 py-3">Source</th>
              <th className="text-left px-4 py-3">Démarré</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={7} className="text-center py-12 text-gray-600">Chargement...</td></tr>
            )}
            {!isLoading && alerts.length === 0 && (
              <tr><td colSpan={7} className="text-center py-12 text-gray-600">✓ Aucune alerte trouvée</td></tr>
            )}
            {alerts.map((alert: any) => (
              <tr key={alert.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3">
                  <p className="font-medium text-white truncate max-w-48">{alert.name}</p>
                  {alert.summary && <p className="text-xs text-gray-500 truncate max-w-48">{alert.summary}</p>}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${SEV_BADGE[alert.severity]}`}>
                    {alert.severity?.toUpperCase()}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_BADGE[alert.status]}`}>
                    {alert.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400 text-xs">{alert.instance || '—'}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{alert.source}</td>
                <td className="px-4 py-3 text-gray-500 text-xs">{alert.started_at?.slice(0, 16)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center gap-2 justify-end">
                    <button onClick={() => setSelected(alert)} className="text-gray-500 hover:text-blue-400 p-1"><Eye size={14} /></button>
                    {alert.status === 'active' && (
                      <>
                        <button onClick={() => ack.mutate(alert.id)} className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded hover:bg-yellow-500/30">ACK</button>
                        <button onClick={() => resolve.mutate(alert.id)} className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded hover:bg-green-500/30">Résoudre</button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail panel */}
      {selected && (
        <div className="fixed inset-0 bg-black/60 z-50 flex justify-end" onClick={() => setSelected(null)}>
          <div className="w-full max-w-xl bg-gray-900 border-l border-gray-700 h-full overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white">Détail alerte</h2>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white"><X size={18} /></button>
            </div>
            <div className="space-y-4">
              <div><label className="text-xs text-gray-500">Nom</label><p className="text-white font-medium mt-1">{selected.name}</p></div>
              <div className="grid grid-cols-2 gap-4">
                <div><label className="text-xs text-gray-500">Sévérité</label>
                  <div className="mt-1"><span className={`text-xs px-2 py-0.5 rounded font-medium ${SEV_BADGE[selected.severity]}`}>{selected.severity?.toUpperCase()}</span></div>
                </div>
                <div><label className="text-xs text-gray-500">Statut</label>
                  <div className="mt-1"><span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_BADGE[selected.status]}`}>{selected.status}</span></div>
                </div>
              </div>
              <div><label className="text-xs text-gray-500">Instance</label><p className="text-gray-300 mt-1">{selected.instance || '—'}</p></div>
              <div><label className="text-xs text-gray-500">Résumé</label><p className="text-gray-300 mt-1">{selected.summary || '—'}</p></div>
              <div><label className="text-xs text-gray-500">Description</label><p className="text-gray-300 mt-1">{selected.description || '—'}</p></div>
              {selected.labels && Object.keys(selected.labels).length > 0 && (
                <div><label className="text-xs text-gray-500">Labels</label>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {Object.entries(selected.labels).map(([k, v]: any) => (
                      <span key={k} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded">{k}={v}</span>
                    ))}
                  </div>
                </div>
              )}
              <div><label className="text-xs text-gray-500">Source</label><p className="text-gray-300 mt-1">{selected.source}</p></div>
              <div><label className="text-xs text-gray-500">Démarré le</label><p className="text-gray-300 mt-1">{selected.started_at}</p></div>
              {selected.status === 'active' && (
                <div className="flex gap-3 pt-4 border-t border-gray-800">
                  <button onClick={() => { ack.mutate(selected.id); setSelected(null) }}
                    className="flex-1 bg-yellow-600 hover:bg-yellow-700 text-white py-2 rounded-lg text-sm font-medium">Acknowledger</button>
                  <button onClick={() => { resolve.mutate(selected.id); setSelected(null) }}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg text-sm font-medium">Résoudre</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
