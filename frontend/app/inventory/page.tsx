'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { inventoryApi } from '@/lib/api'
import { Server, Plus, ChevronRight, Globe, Layers, Cpu, X, Edit2, Trash2 } from 'lucide-react'

const STATUS_COLOR: Record<string, string> = {
  active: 'bg-green-500', inactive: 'bg-gray-500',
  maintenance: 'bg-yellow-500', decommissioned: 'bg-red-500',
}
const TYPE_COLOR: Record<string, string> = {
  production: 'text-red-400 bg-red-500/10',
  staging: 'text-orange-400 bg-orange-500/10',
  development: 'text-blue-400 bg-blue-500/10',
  testing: 'text-purple-400 bg-purple-500/10',
}

function Modal({ open, onClose, title, children }: any) {
  if (!open) return null
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-bold text-white">{title}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Field({ label, children }: any) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  )
}

const inp = "w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"

export default function InventoryPage() {
  const qc = useQueryClient()
  const [selectedDC, setSelectedDC] = useState<any>(null)
  const [selectedEnv, setSelectedEnv] = useState<any>(null)
  const [modal, setModal] = useState<string | null>(null)
  const [form, setForm] = useState<any>({})

  const { data: datacenters = [] } = useQuery({ queryKey: ['datacenters'], queryFn: inventoryApi.listDatacenters })
  const { data: environments = [] } = useQuery({ queryKey: ['environments', selectedDC?.id], queryFn: () => inventoryApi.listEnvironments(selectedDC?.id), enabled: true })
  const { data: servers = [] } = useQuery({ queryKey: ['servers', selectedEnv?.id], queryFn: () => inventoryApi.listServers({ environment_id: selectedEnv?.id }), enabled: true })
  const { data: stats } = useQuery({ queryKey: ['invStats'], queryFn: inventoryApi.getStats })

  const createDC = useMutation({ mutationFn: inventoryApi.createDatacenter, onSuccess: () => { qc.invalidateQueries({ queryKey: ['datacenters'] }); setModal(null) } })
  const createEnv = useMutation({ mutationFn: inventoryApi.createEnvironment, onSuccess: () => { qc.invalidateQueries({ queryKey: ['environments'] }); setModal(null) } })
  const createSrv = useMutation({ mutationFn: inventoryApi.createServer, onSuccess: () => { qc.invalidateQueries({ queryKey: ['servers'] }); setModal(null) } })
  const deleteSrv = useMutation({ mutationFn: inventoryApi.deleteServer, onSuccess: () => qc.invalidateQueries({ queryKey: ['servers'] }) })

  const openModal = (type: string, defaults: any = {}) => { setForm(defaults); setModal(type) }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Server size={22} className="text-blue-400" /> Inventaire</h1>
          <p className="text-gray-400 text-sm mt-1">Infrastructure — Datacenters, Environments, Serveurs</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { l: 'Datacenters', v: stats?.datacenters ?? 0, icon: Globe },
          { l: 'Environments', v: stats?.environments ?? 0, icon: Layers },
          { l: 'Serveurs', v: stats?.servers ?? 0, icon: Server },
          { l: 'Composants', v: stats?.components ?? 0, icon: Cpu },
        ].map(({ l, v, icon: Icon }) => (
          <div key={l} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center gap-3">
            <Icon size={20} className="text-blue-400" />
            <div><p className="text-xl font-bold text-white">{v}</p><p className="text-xs text-gray-500">{l}</p></div>
          </div>
        ))}
      </div>

      {/* 3-column layout */}
      <div className="grid grid-cols-3 gap-4">
        {/* Datacenters */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2"><Globe size={14} /> Datacenters</h3>
            <button onClick={() => openModal('dc')} className="text-blue-400 hover:text-blue-300"><Plus size={16} /></button>
          </div>
          <div className="divide-y divide-gray-800">
            {datacenters.map((dc: any) => (
              <div key={dc.id} onClick={() => { setSelectedDC(dc); setSelectedEnv(null) }}
                className={`px-4 py-3 cursor-pointer flex items-center justify-between hover:bg-gray-800 transition-colors ${selectedDC?.id === dc.id ? 'bg-blue-600/20 border-l-2 border-blue-500' : ''}`}>
                <div>
                  <p className="text-sm text-white font-medium">{dc.name}</p>
                  <p className="text-xs text-gray-500">{dc.location || '—'}</p>
                </div>
                <ChevronRight size={14} className="text-gray-600" />
              </div>
            ))}
            {datacenters.length === 0 && <p className="text-center py-8 text-gray-600 text-sm">Aucun datacenter</p>}
          </div>
        </div>

        {/* Environments */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2"><Layers size={14} /> Environments {selectedDC && `— ${selectedDC.name}`}</h3>
            {selectedDC && <button onClick={() => openModal('env', { datacenter_id: selectedDC.id })} className="text-blue-400 hover:text-blue-300"><Plus size={16} /></button>}
          </div>
          <div className="divide-y divide-gray-800">
            {environments.filter((e: any) => !selectedDC || e.datacenter_id === selectedDC.id).map((env: any) => (
              <div key={env.id} onClick={() => setSelectedEnv(env)}
                className={`px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors ${selectedEnv?.id === env.id ? 'bg-blue-600/20 border-l-2 border-blue-500' : ''}`}>
                <div className="flex items-center justify-between">
                  <p className="text-sm text-white font-medium">{env.name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${TYPE_COLOR[env.type]}`}>{env.type}</span>
                </div>
                {env.description && <p className="text-xs text-gray-500 mt-0.5 truncate">{env.description}</p>}
              </div>
            ))}
            {!selectedDC && <p className="text-center py-8 text-gray-600 text-sm">← Sélectionner un datacenter</p>}
          </div>
        </div>

        {/* Servers */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2"><Server size={14} /> Serveurs {selectedEnv && `— ${selectedEnv.name}`}</h3>
            {selectedEnv && <button onClick={() => openModal('server', { environment_id: selectedEnv.id })} className="text-blue-400 hover:text-blue-300"><Plus size={16} /></button>}
          </div>
          <div className="divide-y divide-gray-800 overflow-y-auto max-h-96">
            {servers.filter((s: any) => !selectedEnv || s.environment_id === selectedEnv.id).map((srv: any) => (
              <div key={srv.id} className="px-4 py-3 hover:bg-gray-800 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${STATUS_COLOR[srv.status]}`} />
                    <p className="text-sm text-white font-medium">{srv.hostname}</p>
                  </div>
                  <button onClick={() => deleteSrv.mutate(srv.id)} className="text-gray-600 hover:text-red-400"><Trash2 size={13} /></button>
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                  <span>{srv.ip_address || '—'}</span>
                  {srv.os_type && <span>{srv.os_type}</span>}
                  {srv.cpu_cores && <span>{srv.cpu_cores} CPU</span>}
                  {srv.ram_gb && <span>{srv.ram_gb}GB RAM</span>}
                </div>
                {srv.maintenance_mode && <span className="text-xs text-yellow-400">⚠ Maintenance</span>}
              </div>
            ))}
            {!selectedEnv && <p className="text-center py-8 text-gray-600 text-sm">← Sélectionner un environment</p>}
          </div>
        </div>
      </div>

      {/* Modal DC */}
      <Modal open={modal === 'dc'} onClose={() => setModal(null)} title="Nouveau Datacenter">
        <div className="space-y-4">
          <Field label="Nom *"><input className={inp} value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="DC-Paris-01" /></Field>
          <Field label="Localisation"><input className={inp} value={form.location || ''} onChange={e => setForm({ ...form, location: e.target.value })} placeholder="Paris, France" /></Field>
          <Field label="Description"><textarea className={inp} rows={2} value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })} /></Field>
          <button onClick={() => createDC.mutate(form)} disabled={!form.name} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer</button>
        </div>
      </Modal>

      {/* Modal Env */}
      <Modal open={modal === 'env'} onClose={() => setModal(null)} title="Nouvel Environment">
        <div className="space-y-4">
          <Field label="Nom *"><input className={inp} value={form.name || ''} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="prod-web" /></Field>
          <Field label="Type">
            <select className={inp} value={form.type || 'development'} onChange={e => setForm({ ...form, type: e.target.value })}>
              {['production','staging','development','testing'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Description"><textarea className={inp} rows={2} value={form.description || ''} onChange={e => setForm({ ...form, description: e.target.value })} /></Field>
          <button onClick={() => createEnv.mutate(form)} disabled={!form.name} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer</button>
        </div>
      </Modal>

      {/* Modal Server */}
      <Modal open={modal === 'server'} onClose={() => setModal(null)} title="Nouveau Serveur">
        <div className="space-y-4">
          <Field label="Hostname *"><input className={inp} value={form.hostname || ''} onChange={e => setForm({ ...form, hostname: e.target.value })} placeholder="web-01.prod.local" /></Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="IP"><input className={inp} value={form.ip_address || ''} onChange={e => setForm({ ...form, ip_address: e.target.value })} placeholder="192.168.1.10" /></Field>
            <Field label="OS">
              <select className={inp} value={form.os_type || ''} onChange={e => setForm({ ...form, os_type: e.target.value })}>
                <option value="">— Choisir —</option>
                {['Ubuntu','Debian','CentOS','RHEL','Windows Server','Oracle Linux'].map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <Field label="CPU Cores"><input type="number" className={inp} value={form.cpu_cores || ''} onChange={e => setForm({ ...form, cpu_cores: parseInt(e.target.value) })} /></Field>
            <Field label="RAM (GB)"><input type="number" className={inp} value={form.ram_gb || ''} onChange={e => setForm({ ...form, ram_gb: parseFloat(e.target.value) })} /></Field>
            <Field label="Disk (GB)"><input type="number" className={inp} value={form.disk_gb || ''} onChange={e => setForm({ ...form, disk_gb: parseFloat(e.target.value) })} /></Field>
          </div>
          <button onClick={() => createSrv.mutate(form)} disabled={!form.hostname} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium">Créer</button>
        </div>
      </Modal>
    </div>
  )
}
