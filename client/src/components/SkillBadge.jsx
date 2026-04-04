const COLORS = {
  Remote: 'bg-green-500/15 text-green-400 border-green-500/25',
  Hybrid: 'bg-amber-500/15 text-amber-400 border-amber-500/25',
  'On-site': 'bg-slate-500/15 text-slate-400 border-slate-500/25',
  Entry: 'bg-blue-500/15 text-blue-400 border-blue-500/25',
  Mid: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/25',
  Senior: 'bg-purple-500/15 text-purple-400 border-purple-500/25',
  Lead: 'bg-pink-500/15 text-pink-400 border-pink-500/25',
  Principal: 'bg-rose-500/15 text-rose-400 border-rose-500/25',
  Staff: 'bg-red-500/15 text-red-400 border-red-500/25',
}

export default function SkillBadge({ label, variant }) {
  const cls = COLORS[variant || label] || 'bg-brand-500/15 text-brand-400 border-brand-500/25'
  return (
    <span className={`badge border text-xs ${cls}`}>{label}</span>
  )
}
