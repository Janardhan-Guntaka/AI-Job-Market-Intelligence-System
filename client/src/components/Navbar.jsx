import { useLocation, useNavigate } from 'react-router-dom'
import { Bell, Search, Sparkles } from 'lucide-react'

const PAGE_TITLES = {
  '/dashboard': { title: 'Dashboard', sub: 'Market overview & real-time insights' },
  '/jobs': { title: 'Job Explorer', sub: 'Browse and filter 500+ live positions' },
  '/analytics': { title: 'Analytics', sub: 'Deep-dive salary, skill & hiring trends' },
}

export default function Navbar() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const info = PAGE_TITLES[pathname] || { title: 'AI Job Intel', sub: '' }

  const handleSearch = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      navigate(`/jobs?q=${encodeURIComponent(e.target.value.trim())}`)
      e.target.value = '' // clear after search
    }
  }

  return (
    <header
      id="navbar"
      className="fixed top-0 left-64 right-0 z-30 px-6 py-4"
      style={{
        background: 'rgba(4, 13, 26, 0.85)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-400" />
            {info.title}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">{info.sub}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              id="navbar-search"
              type="text"
              placeholder="Quick search (Press Enter)..."
              onKeyDown={handleSearch}
              className="pl-8 pr-4 py-2 text-xs rounded-xl bg-surface-700 border border-white/8 text-slate-300
                         placeholder-slate-600 focus:outline-none focus:border-brand-500 w-52 transition-colors"
            />
          </div>
          <button id="navbar-notifications" className="relative p-2 rounded-xl bg-surface-700 border border-white/8 hover:border-brand-500/50 transition-colors">
            <Bell className="w-4 h-4 text-slate-400" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-brand-500" />
          </button>
          <div className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white"
            style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)' }}>
            JG
          </div>
        </div>
      </div>
    </header>
  )
}
