export default function KPICard({ id, icon: Icon, label, value, sub, color = 'blue', trend }) {
  const colors = {
    blue: { border: 'rgba(59,130,246,0.3)', glow: 'rgba(59,130,246,0.1)', icon: '#3b82f6', badge: 'bg-blue-500/10 text-blue-400' },
    purple: { border: 'rgba(139,92,246,0.3)', glow: 'rgba(139,92,246,0.1)', icon: '#8b5cf6', badge: 'bg-purple-500/10 text-purple-400' },
    green: { border: 'rgba(34,197,94,0.3)', glow: 'rgba(34,197,94,0.1)', icon: '#22c55e', badge: 'bg-green-500/10 text-green-400' },
    amber: { border: 'rgba(245,158,11,0.3)', glow: 'rgba(245,158,11,0.1)', icon: '#f59e0b', badge: 'bg-amber-500/10 text-amber-400' },
  }
  const c = colors[color]

  return (
    <div
      id={id}
      className="glass-card p-5 transition-all duration-300 hover:-translate-y-1 animate-slide-up"
      style={{ borderColor: c.border, boxShadow: `0 4px 24px ${c.glow}` }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: c.glow, border: `1px solid ${c.border}` }}>
          <Icon size={20} style={{ color: c.icon }} />
        </div>
        {trend !== undefined && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${c.badge}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white mt-2">{value}</p>
      <p className="text-sm font-medium text-slate-300 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )
}
