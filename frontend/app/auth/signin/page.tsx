'use client'
import { useState } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { Shield, Loader } from 'lucide-react'

export default function SignInPage() {
  const router = useRouter()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    setError('')
    const res = await signIn('credentials', { ...form, redirect: false })
    if (res?.ok) {
      router.push('/dashboard')
    } else {
      setError('Identifiants invalides')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">RAXUS</h1>
          <p className="text-gray-500 text-sm mt-1">Unified IT Operations Platform</p>
        </div>

        {/* Form */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Utilisateur</label>
            <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })}
              placeholder="admin"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Mot de passe</label>
            <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              onKeyDown={e => e.key === 'Enter' && handleSubmit()} />
          </div>

          {error && <p className="text-xs text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{error}</p>}

          <button onClick={handleSubmit} disabled={loading || !form.username || !form.password}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors">
            {loading ? <><Loader size={14} className="animate-spin" /> Connexion...</> : 'Se connecter'}
          </button>

          <p className="text-xs text-gray-600 text-center">Compte par défaut: admin / password</p>
        </div>
      </div>
    </div>
  )
}
