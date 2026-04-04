import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, BriefcaseBusiness, BarChart3,
  Brain, TrendingUp, Zap
} from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/jobs', icon: BriefcaseBusiness, label: 'Job Explorer' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
]

export default function Sidebar() {
  return (
    <aside
      id="sidebar"
      className="fixed left-0 top-0 h-full w-64 z-40"
      style={{
        background: 'linear-gradient(180deg, #071224 0%, #040d1a 100%)',
        borderRight: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/5">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center"
          style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)' }}>
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="font-bold text-sm text-white leading-tight">AI Job Intel</p>
          <p className="text-xs text-slate-500">Market Intelligence</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="px-3 mt-6 space-y-1">
        <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider px-3 mb-3">Main Menu</p>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            id={`nav-${label.toLowerCase().replace(' ', '-')}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'text-white bg-brand-600/20 border border-brand-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`
            }
          >
            <Icon className="w-4.5 h-4.5 flex-shrink-0" size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom status */}
      <div className="absolute bottom-6 left-0 right-0 px-6">
        <div className="glass-card p-3">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-3.5 h-3.5 text-brand-400" />
            <span className="text-xs font-semibold text-slate-300">Live Data</span>
            <span className="ml-auto w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
          </div>
          <p className="text-xs text-slate-500">500+ jobs indexed</p>
          <div className="mt-2 h-1 rounded-full bg-surface-600">
            <div className="h-full w-3/4 rounded-full"
              style={{ background: 'linear-gradient(90deg, #2563eb, #7c3aed)' }} />
          </div>
        </div>
      </div>
    </aside>
  )
}
