import { useEffect, useState } from 'react'
import {
  BriefcaseBusiness, DollarSign, Wifi, TrendingUp, Users, Award
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import KPICard from '../components/KPICard'
import { fetchSummary, fetchTrends, fetchSkillStats } from '../api/client'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 text-xs border-brand-500/30">
      <p className="text-slate-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="font-semibold">
          {p.name}: {typeof p.value === 'number' && p.value > 1000
            ? `$${(p.value / 1000).toFixed(0)}k`
            : p.value}
        </p>
      ))}
    </div>
  )
}

function fmt(n) {
  if (!n) return '—'
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(0)}k`
  return `$${n}`
}

const SKILL_COLORS = [
  '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#6366f1', '#14b8a6', '#f97316',
]

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [trends, setTrends] = useState([])
  const [skills, setSkills] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchSummary(), fetchTrends(), fetchSkillStats()])
      .then(([s, t, sk]) => {
        setSummary(s.data)
        setTrends(t.data)
        setSkills(sk.data.slice(0, 10))
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div id="dashboard-loading" className="flex items-center justify-center h-80">
        <div className="text-center">
          <div className="w-10 h-10 rounded-full border-2 border-brand-500 border-t-transparent animate-spin mx-auto mb-3" />
          <p className="text-slate-500 text-sm">Loading market data…</p>
        </div>
      </div>
    )
  }

  const avgSalary = summary
    ? Math.round((summary.avg_salary_min + summary.avg_salary_max) / 2)
    : 0

  return (
    <div id="dashboard" className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            Market <span className="gradient-text">Intelligence</span>
          </h2>
          <p className="text-slate-500 text-sm mt-1">Real-time insights across {Object.keys(summary?.categories || {}).length} job categories</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
          Live • Updated just now
        </div>
      </div>

      {/* KPI cards */}
      <div id="kpi-cards" className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard id="kpi-total-jobs" icon={BriefcaseBusiness} label="Total Jobs" value={summary?.total_jobs?.toLocaleString() || '—'} sub="Active listings" color="blue" trend={12} />
        <KPICard id="kpi-avg-salary" icon={DollarSign} label="Avg Salary" value={fmt(avgSalary)} sub="Across all roles" color="green" trend={8} />
        <KPICard id="kpi-remote-jobs" icon={Wifi} label="Remote Roles" value={`${summary?.remote_pct || 0}%`} sub={`${summary?.remote_jobs || 0} positions`} color="purple" trend={5} />
        <KPICard id="kpi-categories" icon={Award} label="Categories" value={Object.keys(summary?.categories || {}).length} sub="Specializations" color="amber" trend={2} />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Trend Chart */}
        <div className="glass-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-semibold text-white text-sm">Hiring Trend</h3>
              <p className="text-xs text-slate-500 mt-0.5">Weekly job postings (last 12 weeks)</p>
            </div>
            <TrendingUp className="w-4 h-4 text-brand-400" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trends} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="count" name="Jobs Posted" stroke="#3b82f6" strokeWidth={2} fill="url(#trendGrad)" dot={false} activeDot={{ r: 4, fill: '#3b82f6' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Category breakdown */}
        <div className="glass-card p-5">
          <h3 className="font-semibold text-white text-sm mb-1">Category Breakdown</h3>
          <p className="text-xs text-slate-500 mb-4">Jobs by department</p>
          <div className="space-y-2.5">
            {Object.entries(summary?.categories || {})
              .sort(([, a], [, b]) => b - a)
              .slice(0, 7)
              .map(([cat, count], i) => {
                const total = summary?.total_jobs || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={cat}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-300 truncate max-w-[130px]">{cat}</span>
                      <span className="text-slate-500">{count}</span>
                    </div>
                    <div className="h-1.5 bg-surface-600 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: SKILL_COLORS[i % SKILL_COLORS.length] }}
                      />
                    </div>
                  </div>
                )
              })}
          </div>
        </div>
      </div>

      {/* Top Skills bar chart */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h3 className="font-semibold text-white text-sm">Top 10 In-Demand Skills</h3>
            <p className="text-xs text-slate-500 mt-0.5">Ranked by job listing frequency</p>
          </div>
          <Users className="w-4 h-4 text-purple-400" />
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={skills} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis dataKey="skill" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="count" name="Job Count" radius={[4, 4, 0, 0]}>
              {skills.map((_, i) => (
                <Cell key={i} fill={SKILL_COLORS[i % SKILL_COLORS.length]} opacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
