'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Bell, Server, Activity, CheckSquare, BarChart2,
  Mail, GitBranch, Ticket, Settings, Users, Menu, X,
  LogOut, ChevronDown, AlertTriangle, Shield
} from 'lucide-react'

const nav = [
  { href: '/dashboard', label: 'Dashboard', icon: Activity },
  { href: '/alerts', label: 'Alertes', icon: Bell },
  { href: '/inventory', label: 'Inventaire', icon: Server },
  { href: '/tasks', label: 'Tâches', icon: CheckSquare },
  { href: '/slo', label: 'SLO / Probes', icon: BarChart2 },
  { href: '/tickets', label: 'Tickets', icon: Ticket },
  { href: '/rules', label: 'Règles', icon: GitBranch },
  { href: '/notifications', label: 'Notifications', icon: Mail },
  { href: '/users', label: 'Utilisateurs', icon: Users },
  { href: '/settings', label: 'Paramètres', icon: Settings },
]

const severityColor: Record<string, string> = {
  critical: 'bg-red-500', major: 'bg-orange-500',
  minor: 'bg-yellow-500', warning: 'bg-blue-500', info: 'bg-green-500',
}

export default function Sidebar({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mobile, setMobile] = useState(false)

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className={`flex flex-col border-r border-gray-800 bg-gray-900 transition-all duration-200 ${collapsed ? 'w-16' : 'w-60'}`}>
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800 h-16">
          {!collapsed && (
            <div className="flex items-center gap-2">
              <Shield className="text-blue-400" size={22} />
              <span className="font-bold text-lg tracking-wide text-white">RAXUS</span>
            </div>
          )}
          {collapsed && <Shield className="text-blue-400 mx-auto" size={22} />}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-400 hover:text-white ml-auto"
          >
            {collapsed ? <Menu size={18} /> : <X size={18} />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname?.startsWith(href)
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  active
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <Icon size={18} className="shrink-0" />
                {!collapsed && <span>{label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User */}
        <div className={`p-3 border-t border-gray-800 ${collapsed ? 'flex justify-center' : ''}`}>
          <button className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white text-sm">
            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white shrink-0">A</div>
            {!collapsed && <span>Admin</span>}
            {!collapsed && <LogOut size={14} className="ml-auto" />}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-950">
        {children}
      </main>
    </div>
  )
}
