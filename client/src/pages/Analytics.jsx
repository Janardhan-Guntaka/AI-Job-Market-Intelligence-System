import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, PolarGrid,
  PolarAngleAxis, Radar, LineChart, Line, Legend
} from 'recharts'
import { fetchSalaryStats, fetchSkillStats, fetchTrends } from '../api/client'

const COLORS = [
  '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981',
  '#f59e0b', '#ef4444', '#ec4899', '#6366f1',
]

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 text-xs border-brand-500/30 shadow-xl">
      <p className="text-slate-400 mb-1 font-medium">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="font-semibold">
          {p.name}:{' '}
          {typeof p.value === 'number' && p.value > 1000
            ? `$${(p.value / 1000).toFixed(0)}k`
            : p.value}
        </p>
      ))}
    </div>
  )
}

function SectionTitle({ title, sub }) {
  return (
    <div className="mb-5">
      <h3 className="font-semibold text-white text-sm">{title}</h3>
      <p className="text-xs text-slate-500 mt-0.5">{sub}</p>
    </div>
  )
}

export default function Analytics() {
  const [salaryData, setSalaryData] = useState([])
  const [skillData, setSkillData] = useState([])
  const [trendData, setTrendData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchSalaryStats(), fetchSkillStats(), fetchTrends()])
      .then(([s, sk, t]) => {
        setSalaryData(s.data.sort((a, b) => b.avg_max - a.avg_max))
        setSkillData(
          sk.data.slice(0, 8).map(d => ({
            skill: d.skill,
            demand: d.count,
            salary: Math.round(d.avg_salary / 1000),
          }))
        )
        setTrendData(t.data)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div id="analytics-loading" className="flex items-center justify-center h-80">
        <div className="w-10 h-10 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      </div>
    )
  }

  return (
    <div id="analytics" className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">
          Deep <span className="gradient-text">Analytics</span>
        </h2>
        <p className="text-slate-500 text-sm mt-1">Salary benchmarks, skill demand, and hiring velocity</p>
      </div>

      {/* Salary by category */}
      <div className="glass-card p-5">
        <SectionTitle
          title="Salary Range by Category"
          sub="Average min & max compensation (USD/year)"
        />
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={salaryData} margin={{ top: 5, right: 20, left: 10, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis
              dataKey="category"
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              angle={-30}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              tick={{ fill: '#64748b', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 16 }}
            />
            <Bar dataKey="avg_min" name="Avg Min" fill="#3b82f6" radius={[3, 3, 0, 0]} opacity={0.7} />
            <Bar dataKey="avg_max" name="Avg Max" fill="#8b5cf6" radius={[3, 3, 0, 0]} opacity={0.85} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Two column: radar + trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Skill Radar */}
        <div className="glass-card p-5">
          <SectionTitle
            title="Skill Demand Radar"
            sub="Top 8 skills by market frequency"
          />
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={skillData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fill: '#94a3b8', fontSize: 10 }}
              />
              <Radar
                name="Demand"
                dataKey="demand"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Radar
                name="Avg Salary (k)"
                dataKey="salary"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Hiring Velocity (Salary over time) */}
        <div className="glass-card p-5">
          <SectionTitle
            title="Hiring Velocity"
            sub="Weekly postings & avg salary over 12 weeks"
          />
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData} margin={{ top: 5, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: '#64748b', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => `$${(v / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="count"
                name="Jobs/Week"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="avg_salary"
                name="Avg Salary"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top skills table */}
      <div className="glass-card p-5">
        <SectionTitle
          title="Skills Intelligence Table"
          sub="Demand count and average salary per skill"
        />
        <div className="overflow-x-auto">
          <table id="skills-table" className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                {['Rank', 'Skill', 'Job Count', 'Avg Salary', 'Demand Score'].map(h => (
                  <th key={h} className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider pb-3 pr-4 last:pr-0">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/4">
              {skillData.map((s, i) => {
                const maxDemand = skillData[0]?.demand || 1
                const pct = Math.round((s.demand / maxDemand) * 100)
                return (
                  <tr key={s.skill} className="hover:bg-white/2 transition-colors">
                    <td className="py-3 pr-4 text-slate-500 font-mono text-xs">#{i + 1}</td>
                    <td className="py-3 pr-4 font-medium text-slate-200">{s.skill}</td>
                    <td className="py-3 pr-4 text-slate-300">{s.demand.toLocaleString()}</td>
                    <td className="py-3 pr-4 text-green-400 font-semibold">${s.salary}k</td>
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-surface-600 rounded-full overflow-hidden max-w-[120px]">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${pct}%`, background: COLORS[i % COLORS.length] }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">{pct}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
