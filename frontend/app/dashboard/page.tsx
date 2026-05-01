'use client'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi, alertsApi } from '@/lib/api'
import { AlertTriangle, Server, BarChart2, CheckSquare, Activity, TrendingUp, Clock, Shield } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

const SEV_COLORS: Record<string, string> = {
  critical: '#EF4444', major: '#F97316', minor: '#EAB308', warning: '#3B82F6', info: '#22C55E'
}

function StatCard({ title, value, sub, icon: Icon, color = 'blue' }: any) {
  const colors: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-400/10', red: 'text-red-400 bg-red-400/10',
    green: 'text-green-400 bg-green-400/10', orange: 'text-orange-400 bg-orange-400/10',
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-gray-400">{title}</span>
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon size={18} />
        </div>
      </div>
      <p className="text-3xl font-bold text-white">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    major: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    minor: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    warning: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    info: 'bg-green-500/20 text-green-400 border-green-500/30',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${colors[severity] || ''}`}>
      {severity?.toUpperCase()}
    </span>
  )
}

export default function DashboardPage() {
  const { data: summary } = useQuery({ queryKey: ['dashboard'], queryFn: dashboardApi.getSummary, refetchInterval: 30_000 })
  const { data: timeline } = useQuery({ queryKey: ['timeline'], queryFn: () => dashboardApi.getTimeline(7) })
  const { data: topIssues } = useQuery({ queryKey: ['topIssues'], queryFn: dashboardApi.getTopIssues })
  const { data: recentAlerts } = useQuery({ queryKey: ['recentAlerts'], queryFn: () => alertsApi.list({ limit: 8, status: 'active' }) })

  const alertStats = summary?.alerts || {}
  const invStats = summary?.inventory || {}
  const sloStats = summary?.slo || {}
  const taskStats = summary?.tasks || {}

  // Transform timeline for chart
  const timelineData = timeline?.reduce((acc: any[], row: any) => {
    const existing = acc.find((d: any) => d.date === row.date)
    if (existing) { existing[row.severity] = row.count }
    else { acc.push({ date: row.date, [row.severity]: row.count }) }
    return acc
  }, []) || []

  const pieData = Object.entries(alertStats.by_severity || {}).map(([k, v]) => ({ name: k, value: v }))

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Vue d'ensemble de votre infrastructure</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          Temps réel
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Alertes actives" value={alertStats.active ?? 0} sub={`${alertStats.total ?? 0} total`} icon={AlertTriangle} color={alertStats.active > 0 ? 'red' : 'green'} />
        <StatCard title="Serveurs" value={invStats.servers ?? 0} sub={`${invStats.in_maintenance ?? 0} en maintenance`} icon={Server} color="blue" />
        <StatCard title="SLO / Probes" value={sloStats.probes_up ?? 0} sub={`${sloStats.probes_down ?? 0} down`} icon={BarChart2} color={sloStats.probes_down > 0 ? 'orange' : 'green'} />
        <StatCard title="Tâches aujourd'hui" value={(taskStats.success_today ?? 0) + (taskStats.failed_today ?? 0)} sub={`${taskStats.running ?? 0} en cours`} icon={CheckSquare} color="blue" />
      </div>

      {/* Second row stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Datacenters" value={invStats.datacenters ?? 0} icon={Shield} color="blue" />
        <StatCard title="Environments" value={invStats.environments ?? 0} icon={Activity} color="blue" />
        <StatCard title="Critical" value={alertStats.by_severity?.critical ?? 0} icon={AlertTriangle} color="red" />
        <StatCard title="SLO targets" value={sloStats.slo_targets ?? 0} icon={TrendingUp} color="green" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Timeline */}
        <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4">Alertes sur 7 jours</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#9CA3AF' }} />
              <YAxis tick={{ fontSize: 11, fill: '#9CA3AF' }} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
              <Area type="monotone" dataKey="critical" stackId="1" stroke="#EF4444" fill="#EF444430" />
              <Area type="monotone" dataKey="major" stackId="1" stroke="#F97316" fill="#F9731630" />
              <Area type="monotone" dataKey="warning" stackId="1" stroke="#3B82F6" fill="#3B82F630" />
              <Area type="monotone" dataKey="info" stackId="1" stroke="#22C55E" fill="#22C55E30" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Pie by severity */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-4">Distribution sévérité</h3>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={140}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={SEV_COLORS[entry.name] || '#6B7280'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 mt-2">
                {pieData.map(({ name, value }) => (
                  <div key={name} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: SEV_COLORS[name] }} />
                      <span className="text-gray-400 capitalize">{name}</span>
                    </div>
                    <span className="text-white font-medium">{value as number}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-600 text-sm">Aucune donnée</div>
          )}
        </div>
      </div>

      {/* Recent Alerts + Top Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent alerts */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-300">Alertes actives récentes</h3>
            <a href="/alerts" className="text-xs text-blue-400 hover:underline">Voir tout →</a>
          </div>
          <div className="space-y-2">
            {(recentAlerts || []).slice(0, 7).map((alert: any) => (
              <div key={alert.id} className="flex items-start gap-3 p-2.5 rounded-lg bg-gray-800/50 hover:bg-gray-800 transition-colors">
                <div className="mt-0.5">
                  <SeverityBadge severity={alert.severity} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{alert.name}</p>
                  <p className="text-xs text-gray-500 truncate">{alert.instance || 'N/A'}</p>
                </div>
                <Clock size={12} className="text-gray-600 mt-1 shrink-0" />
              </div>
            ))}
            {(!recentAlerts || recentAlerts.length === 0) && (
              <div className="text-center py-8 text-gray-600 text-sm">✓ Aucune alerte active</div>
            )}
          </div>
        </div>

        {/* Top Issues */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-300">Problèmes fréquents (30j)</h3>
          </div>
          <div className="space-y-2">
            {(topIssues || []).slice(0, 7).map((issue: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-4">{i + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-300 truncate">{issue.name}</span>
                    <span className="text-xs text-gray-500 ml-2 shrink-0">{issue.count}x</span>
                  </div>
                  <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.min(100, (issue.count / (topIssues[0]?.count || 1)) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
            {(!topIssues || topIssues.length === 0) && (
              <div className="text-center py-8 text-gray-600 text-sm">Aucune donnée disponible</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
