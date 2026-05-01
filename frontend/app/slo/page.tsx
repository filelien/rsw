'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sloApi } from '@/lib/api'
import { BarChart2, Plus, Activity, X, TrendingUp } from 'lucide-react'

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"

function ComplianceBadge({ value, target }: { value?: number; target: number }) {
  if (value == null) return <span className="text-gray-500 text-sm">N/A</span>
  const ok = value >= target
  return (
    <div className="flex items-center gap-2">
      <span className={`text-lg font-bold ${ok ? 'text-green-400' : 'text-red-400'}`}>{value.toFixed(2)}%</span>
      <span className="text-xs text-gray-500">/ {target}%</span>
    </div>
  )
}

export default function SLOPage() {
  const qc = useQueryClient()
  const [modal, setModal] = useState<'slo' | 'probe' | null>(null)
  const [form, setForm] = useState<any>({})

  const { data: slos = [] } = useQuery({ queryKey: ['slos'], queryFn: sloApi.list })
  const { data: probes = [] } = useQuery({ queryKey: ['probes'], queryFn: sloApi.listProbes, refetchInterval: 30_000 })
  const { data: stats } = useQuery({ queryKey: ['sloStats'], queryFn: sloApi.getStats })

  const createSlo = useMutation({ mutationFn: sloApi.create, onSuccess: () => { qc.invalidateQueries({ queryKey: ['slos'] }); setModal(null) } })
  const createProbe = useMutation({ mutationFn: sloApi.createProbe, onSuccess: () => { qc.invalidateQueries({ queryKey: ['probes'] }); setModal(null) } })
  const deleteSlo = useMutation({ mutationFn: sloApi.delete, onSuccess: () => qc.invalidateQueries({ queryKey: ['slos'] }) })

  const PROBE_STATUS: Record<string, string> = { up: 'text-green-400', down: 'text-red-400', degraded: 'text-yellow-400', unknown: 'text-gray-500' }
  const PROBE_DOT: Record<string, string> = { up: 'bg-green-400', down: 'bg-red-400', degraded: 'bg-yellow-400', unknown: 'bg-gray-600' }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><BarChart2 size={22} className="text-blue-400" /> SLO & Probes</h1>
          <p className="text-gray-400 text-sm mt-1">Service Level Objectives et monitoring de disponibilité</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setForm({}); setModal('probe') }} className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white px-3 py-2 rounded-lg text-sm">
            <Plus size={14} /> Probe
          </button>
          <button onClick={() => { setForm({}); setModal('slo') }} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm">
            <Plus size={14} /> SLO
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { l: 'SLO Targets', v: stats?.slo_targets ?? 0, c: 'text-white' },
          { l: 'Probes total', v: stats?.probes_total ?? 0, c: 'text-white' },
          { l: 'UP', v: stats?.probes_up ?? 0, c: 'text-green-400' },
          { l: 'DOWN', v: stats?.probes_down ?? 0, c: 'text-red-400' },
        ].map(({ l, v, c }) => (
          <div key={l} className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
            <p className={`text-2xl font-bold ${c}`}>{v}</p>
            <p className="text-xs text-gray-500 mt-1">{l}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* SLOs */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2"><TrendingUp size={14} /> SLO Targets</h3>
          </div>
          <div className="divide-y divide-gray-800">
            {slos.map((slo: any) => (
              <div key={slo.id} className="px-4 py-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-white">{slo.name}</p>
                    <p className="text-xs text-gray-500">{slo.service_name} · {slo.sli_type}</p>
                  </div>
                  <button onClick={() => deleteSlo.mutate(slo.id)} className="text-gray-600 hover:text-red-400 text-xs">✕</button>
                </div>
                <div className="mt-2">
                  <ComplianceBadge value={slo.latest_measurement?.compliance} target={slo.target_percent} />
                  <div className="mt-1 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, slo.latest_measurement?.compliance ?? 0)}%` }} />
                  </div>
                </div>
                {slo.latest_measurement?.error_budget_remaining != null && (
                  <p className="text-xs text-gray-500 mt-1">Budget restant: {slo.latest_measurement.error_budget_remaining.toFixed(2)}%</p>
                )}
              </div>
            ))}
            {slos.length === 0 && <p className="text-center py-10 text-gray-600 text-sm">Aucun SLO configuré</p>}
          </div>
        </div>

        {/* Probes */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2"><Activity size={14} /> Probes</h3>
          </div>
          <div className="divide-y divide-gray-800">
            {probes.map((probe: any) => (
              <div key={probe.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${PROBE_DOT[probe.last_status] || 'bg-gray-600'} ${probe.last_status === 'up' ? 'animate-pulse' : ''}`} />
                  <div>
                    <p className="text-sm text-white font-medium">{probe.name}</p>
                    <p className="text-xs text-gray-500 truncate max-w-48">{probe.target}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${PROBE_STATUS[probe.last_status] || 'text-gray-500'}`}>{probe.last_status?.toUpperCase()}</p>
                  <p className="text-xs text-gray-600">{probe.interval_sec}s interval</p>
                </div>
              </div>
            ))}
            {probes.length === 0 && <p className="text-center py-10 text-gray-600 text-sm">Aucune probe configurée</p>}
          </div>
        </div>
      </div>

      {/* SLO Modal */}
      {modal === 'slo' && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">Nouveau SLO</h2>
              <button onClick={() => setModal(null)}><X size={18} className="text-gray-500" /></button>
            </div>
            <div className="space-y-4">
              <div><label className="block text-xs text-gray-400 mb-1">Nom *</label><input className={inp} value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div><label className="block text-xs text-gray-400 mb-1">Service *</label><input className={inp} value={form.service_name || ''} onChange={e => setForm({ ...form, service_name: e.target.value })} placeholder="api-gateway" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs text-gray-400 mb-1">Type SLI</label>
                  <select className={inp} value={form.sli_type || 'availability'} onChange={e => setForm({ ...form, sli_type: e.target.value })}>
                    {['availability','latency','error_rate','throughput'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select></div>
                <div><label className="block text-xs text-gray-400 mb-1">Cible (%)</label>
                  <input type="number" className={inp} value={form.target_percent || 99.9} min={0} max={100} step={0.01} onChange={e => setForm({ ...form, target_percent: parseFloat(e.target.value) })} /></div>
              </div>
              <div><label className="block text-xs text-gray-400 mb-1">Fenêtre (jours)</label>
                <input type="number" className={inp} value={form.window_days || 30} onChange={e => setForm({ ...form, window_days: parseInt(e.target.value) })} /></div>
              <button onClick={() => createSlo.mutate(form)} disabled={!form.name || !form.service_name} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer SLO</button>
            </div>
          </div>
        </div>
      )}

      {/* Probe Modal */}
      {modal === 'probe' && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setModal(null)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-bold text-white">Nouvelle Probe</h2>
              <button onClick={() => setModal(null)}><X size={18} className="text-gray-500" /></button>
            </div>
            <div className="space-y-4">
              <div><label className="block text-xs text-gray-400 mb-1">Nom *</label><input className={inp} value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs text-gray-400 mb-1">Type</label>
                  <select className={inp} value={form.type || 'http'} onChange={e => setForm({ ...form, type: e.target.value })}>
                    {['http','tcp','icmp','dns'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select></div>
                <div><label className="block text-xs text-gray-400 mb-1">Status attendu</label>
                  <input type="number" className={inp} value={form.expected_status || 200} onChange={e => setForm({ ...form, expected_status: parseInt(e.target.value) })} /></div>
              </div>
              <div><label className="block text-xs text-gray-400 mb-1">Target URL / IP *</label><input className={inp} value={form.target || ''} onChange={e => setForm({ ...form, target: e.target.value })} placeholder="https://api.example.com/health" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><label className="block text-xs text-gray-400 mb-1">Interval (sec)</label><input type="number" className={inp} value={form.interval_sec || 60} onChange={e => setForm({ ...form, interval_sec: parseInt(e.target.value) })} /></div>
                <div><label className="block text-xs text-gray-400 mb-1">Timeout (sec)</label><input type="number" className={inp} value={form.timeout_sec || 10} onChange={e => setForm({ ...form, timeout_sec: parseInt(e.target.value) })} /></div>
              </div>
              <button onClick={() => createProbe.mutate(form)} disabled={!form.name || !form.target} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer Probe</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
