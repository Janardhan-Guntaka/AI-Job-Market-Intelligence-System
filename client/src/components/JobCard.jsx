import { Building2, MapPin, DollarSign, Clock } from 'lucide-react'
import SkillBadge from './SkillBadge'

function formatSalary(n) {
  if (n >= 1000) return `$${(n / 1000).toFixed(0)}k`
  return `$${n}`
}

function daysAgo(dateStr) {
  const d = new Date(dateStr)
  const diff = Math.floor((Date.now() - d.getTime()) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'
  return `${diff}d ago`
}

export default function JobCard({ job, index = 0 }) {
  const skills = (() => { try { return JSON.parse(job.skills) } catch { return [] } })()

  return (
    <div
      className="glass-card-hover p-5 animate-slide-up"
      style={{ animationDelay: `${index * 40}ms` }}
      data-testid="job-card"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white text-sm leading-snug truncate">{job.title}</h3>
          <div className="flex items-center gap-1.5 mt-1 text-slate-400 text-xs">
            <Building2 size={12} className="flex-shrink-0" />
            <span className="font-medium text-slate-300">{job.company}</span>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-bold text-white">
            {formatSalary(job.salary_min)}
            <span className="text-slate-500 font-normal"> – </span>
            {formatSalary(job.salary_max)}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">/year</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        <SkillBadge label={job.remote} />
        <SkillBadge label={job.experience_level} />
        <span className="badge bg-surface-600 text-slate-400 border border-white/8 text-xs flex items-center gap-1">
          <MapPin size={10} />{job.location}
        </span>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {skills.slice(0, 4).map((s) => (
          <span key={s} className="badge bg-brand-500/10 text-brand-400 border border-brand-500/20 text-xs">{s}</span>
        ))}
        {skills.length > 4 && (
          <span className="badge bg-surface-600 text-slate-500 text-xs">+{skills.length - 4}</span>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs font-medium px-2.5 py-1 rounded-lg bg-surface-700 text-slate-400">
          {job.category}
        </span>
        <div className="flex items-center gap-1 text-xs text-slate-600">
          <Clock size={11} />
          {daysAgo(job.posted_date)}
        </div>
      </div>
    </div>
  )
}
