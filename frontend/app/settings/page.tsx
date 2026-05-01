'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '@/lib/api'
import { Settings, Key, Copy, Trash2, Plus, Shield } from 'lucide-react'
import { useState } from 'react'

export default function SettingsPage() {
  const qc = useQueryClient()
  const [keyName, setKeyName] = useState('')
  const [newKey, setNewKey] = useState<string | null>(null)

  const { data: apiKeys = [] } = useQuery({ queryKey: ['apiKeys'], queryFn: authApi.listApiKeys })
  const { data: me } = useQuery({ queryKey: ['me'], queryFn: authApi.me })

  const createKey = useMutation({
    mutationFn: () => authApi.createApiKey(keyName),
    onSuccess: (data) => { setNewKey(data.key); setKeyName(''); qc.invalidateQueries({ queryKey: ['apiKeys'] }) }
  })
  const revokeKey = useMutation({ mutationFn: authApi.revokeApiKey, onSuccess: () => qc.invalidateQueries({ queryKey: ['apiKeys'] }) })

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2"><Settings size={22} className="text-blue-400" /> Paramètres</h1>
        <p className="text-gray-400 text-sm mt-1">Configuration et sécurité du compte</p>
      </div>

      {/* Profile */}
      {me && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2"><Shield size={14} /> Profil utilisateur</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500">Nom: </span><span className="text-white">{me.full_name || '—'}</span></div>
            <div><span className="text-gray-500">Username: </span><span className="text-white">{me.username}</span></div>
            <div><span className="text-gray-500">Email: </span><span className="text-white">{me.email}</span></div>
            <div><span className="text-gray-500">Rôle: </span><span className="text-blue-400 font-medium">{me.role}</span></div>
            <div><span className="text-gray-500">Actif: </span><span className="text-green-400">{me.is_active ? 'Oui' : 'Non'}</span></div>
            <div><span className="text-gray-500">Dernière connexion: </span><span className="text-white">{me.last_login?.slice(0, 16) || 'N/A'}</span></div>
          </div>
        </div>
      )}

      {/* API Keys */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4 flex items-center gap-2"><Key size={14} /> Clés API</h3>
        <div className="flex gap-3 mb-4">
          <input value={keyName} onChange={e => setKeyName(e.target.value)} placeholder="Nom de la clé..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          <button onClick={() => createKey.mutate()} disabled={!keyName}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm">
            <Plus size={14} /> Créer
          </button>
        </div>

        {newKey && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 mb-4">
            <p className="text-xs text-green-400 mb-1">⚠ Copiez cette clé — elle ne sera plus affichée</p>
            <div className="flex items-center gap-2">
              <code className="text-sm text-green-300 flex-1 break-all">{newKey}</code>
              <button onClick={() => navigator.clipboard.writeText(newKey)} className="text-green-400 hover:text-green-300"><Copy size={14} /></button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {apiKeys.map((key: any) => (
            <div key={key.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
              <div>
                <p className="text-sm text-white">{key.name}</p>
                <p className="text-xs text-gray-500">{key.prefix}... · Créé: {key.created_at?.slice(0, 10)}</p>
              </div>
              <button onClick={() => revokeKey.mutate(key.id)} className="text-gray-600 hover:text-red-400"><Trash2 size={14} /></button>
            </div>
          ))}
          {apiKeys.length === 0 && <p className="text-gray-600 text-sm text-center py-4">Aucune clé API</p>}
        </div>
      </div>

      {/* System info */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-sm font-medium text-gray-300 mb-4">À propos de RAXUS</h3>
        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            ['Version', '1.0.0'],
            ['Environnement', process.env.NODE_ENV],
            ['API URL', process.env.NEXT_PUBLIC_API_URL],
            ['Services', 'Gateway · AlertManager · Inventory · Notifier · TaskManager · SLO · Rules'],
          ].map(([k, v]) => (
            <div key={k} className="col-span-1 last:col-span-2">
              <span className="text-gray-500">{k}: </span><span className="text-white">{v}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
