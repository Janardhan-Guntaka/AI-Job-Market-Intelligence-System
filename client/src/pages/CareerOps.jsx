import { useState, useRef, useCallback } from 'react'
import {
  Brain, Upload, Sparkles, Trash2, ChevronRight,
  ExternalLink, CheckCircle2, AlertCircle, Loader2,
  Star, Zap, FileText, X, TrendingUp
} from 'lucide-react'
import { uploadResume, getResumeMatch, getMyResume, deleteResume } from '../api/client'
import SkillBadge from '../components/SkillBadge'

// ─── Helpers ────────────────────────────────────────────────────────────────

function fmt(n) {
  if (!n || n === 0) return '—'
  if (n >= 1000000) return `$${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `$${(n / 1000).toFixed(0)}k`
  return `$${n}`
}

function MatchScore({ pct }) {
  const color =
    pct >= 80 ? '#10b981' :
    pct >= 60 ? '#3b82f6' :
    pct >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="relative w-10 h-10 flex-shrink-0">
        <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
          <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="3" />
          <circle
            cx="18" cy="18" r="15.9" fill="none"
            stroke={color} strokeWidth="3"
            strokeDasharray={`${pct} ${100 - pct}`}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-[9px] font-bold" style={{ color }}>
          {pct}%
        </span>
      </div>
    </div>
  )
}

// ─── Upload Zone ─────────────────────────────────────────────────────────────

function UploadZone({ onFileSelect, isUploading }) {
  const inputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }, [onFileSelect])

  return (
    <div
      onClick={() => !isUploading && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      className="relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300"
      style={{
        borderColor: dragOver ? '#3b82f6' : 'rgba(255,255,255,0.12)',
        background: dragOver ? 'rgba(59,130,246,0.06)' : 'rgba(255,255,255,0.02)',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt"
        className="hidden"
        onChange={(e) => e.target.files[0] && onFileSelect(e.target.files[0])}
      />
      {isUploading ? (
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-10 h-10 text-brand-400 animate-spin" />
          <p className="text-sm text-slate-400">Parsing your resume with AI…</p>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(37,99,235,0.3), rgba(124,58,237,0.3))' }}
          >
            <Upload className="w-6 h-6 text-brand-300" />
          </div>
          <div>
            <p className="font-semibold text-white text-sm">Drop your resume here</p>
            <p className="text-slate-500 text-xs mt-1">PDF, DOCX, or TXT • Max 5 MB</p>
          </div>
          <span className="px-4 py-1.5 rounded-full text-xs font-medium border border-brand-500/40 text-brand-400 hover:bg-brand-500/10 transition-colors">
            Browse Files
          </span>
        </div>
      )}
    </div>
  )
}

// ─── Parsed Resume Card ──────────────────────────────────────────────────────

function ResumeCard({ resume, onDelete, onMatch, isMatching }) {
  return (
    <div
      className="rounded-2xl p-5 border"
      style={{
        background: 'linear-gradient(135deg, rgba(16,185,129,0.06) 0%, rgba(37,99,235,0.06) 100%)',
        borderColor: 'rgba(16,185,129,0.2)',
      }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-green-500/15">
            <FileText className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <p className="font-semibold text-white text-sm">{resume.filename}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {resume.experience_level} • {resume.years_experience}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-green-400" />
          <button
            onClick={onDelete}
            className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/10 transition-all"
            title="Delete resume"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Skills */}
      <div className="mb-4">
        <p className="text-xs text-slate-500 font-medium mb-2">Detected Skills ({resume.skills.length})</p>
        <div className="flex flex-wrap gap-1.5">
          {resume.skills.slice(0, 20).map(skill => (
            <SkillBadge key={skill} skill={skill} />
          ))}
          {resume.skills.length > 20 && (
            <span className="text-xs text-slate-500">+{resume.skills.length - 20} more</span>
          )}
        </div>
      </div>

      {/* Likely Titles */}
      {resume.job_titles?.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-slate-500 font-medium mb-2">Likely Role Matches</p>
          <div className="flex flex-wrap gap-1.5">
            {resume.job_titles.map(t => (
              <span key={t} className="text-xs px-2.5 py-1 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/20">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={onMatch}
        disabled={isMatching}
        id="find-jobs-btn"
        className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
        style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)', color: 'white' }}
      >
        {isMatching ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Matching with AI…</>
        ) : (
          <><Sparkles className="w-4 h-4" /> Find My Best Jobs</>
        )}
      </button>
    </div>
  )
}

// ─── Matched Job Card ─────────────────────────────────────────────────────────

function MatchedJobCard({ job, rank, openaiPowered }) {
  const [expanded, setExpanded] = useState(false)
  const skills = Array.isArray(job.skills) ? job.skills : []
  const hasSalary = job.salary_min > 0 || job.salary_max > 0

  return (
    <div
      className="rounded-2xl border transition-all duration-300 overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)',
        borderColor: rank <= 3 ? 'rgba(59,130,246,0.3)' : 'rgba(255,255,255,0.07)',
      }}
    >
      <div className="p-5">
        <div className="flex items-start gap-3">
          {/* Rank */}
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold"
            style={{
              background: rank === 1 ? 'linear-gradient(135deg,#f59e0b,#ef4444)' :
                          rank === 2 ? 'linear-gradient(135deg,#6366f1,#3b82f6)' :
                          rank === 3 ? 'linear-gradient(135deg,#10b981,#06b6d4)' :
                          'rgba(255,255,255,0.08)',
              color: rank <= 3 ? 'white' : '#64748b',
            }}
          >
            {rank <= 3 ? <Star size={12} fill="currentColor" /> : `#${rank}`}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="font-semibold text-white text-sm leading-snug truncate">{job.title}</h3>
                <p className="text-slate-400 text-xs mt-0.5">{job.company}</p>
              </div>
              <MatchScore pct={job.match_pct} />
            </div>

            {/* Meta row */}
            <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
              <span>{job.location}</span>
              <span className="w-1 h-1 rounded-full bg-slate-600" />
              <span className={job.remote === 'Remote' ? 'text-green-400' : 'text-blue-400'}>{job.remote}</span>
              {hasSalary && (
                <>
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                  <span className="text-green-300 font-medium">
                    {job.salary_min === job.salary_max ? fmt(job.salary_min) : `${fmt(job.salary_min)} – ${fmt(job.salary_max)}`}
                  </span>
                </>
              )}
            </div>

            {/* AI Explanation */}
            <div className="mt-3 flex items-start gap-2">
              <div className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5"
                style={{ background: openaiPowered ? 'rgba(168,85,247,0.2)' : 'rgba(16,185,129,0.15)' }}>
                {openaiPowered ? <Sparkles size={10} className="text-purple-400" /> : <Zap size={10} className="text-green-400" />}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed italic">
                "{job.ai_explanation}"
              </p>
            </div>
          </div>
        </div>

        {/* Skills preview */}
        {skills.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {skills.slice(0, 5).map(s => <SkillBadge key={s} skill={s} />)}
            {skills.length > 5 && (
              <span className="text-xs text-slate-600">+{skills.length - 5}</span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="mt-4 flex items-center gap-2">
          {job.apply_url ? (
            <a
              href={job.apply_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all duration-200 hover:opacity-90"
              style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)', color: 'white' }}
            >
              Apply Now <ExternalLink size={11} />
            </a>
          ) : null}
          <button
            onClick={() => setExpanded(p => !p)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium border border-white/10 text-slate-400 hover:text-white hover:border-white/20 transition-all"
          >
            {expanded ? 'Less' : 'More'} <ChevronRight size={11} className={`transition-transform ${expanded ? 'rotate-90' : ''}`} />
          </button>
          {job.source && (
            <span className="ml-auto text-xs text-slate-600 capitalize">{job.source}</span>
          )}
        </div>

        {/* Expanded description */}
        {expanded && job.description && (
          <div className="mt-3 pt-3 border-t border-white/5">
            <p className="text-xs text-slate-400 leading-relaxed line-clamp-6">
              {job.description.slice(0, 600)}{job.description.length > 600 ? '…' : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function CareerOps() {
  const [resume, setResume] = useState(null)
  const [matchResult, setMatchResult] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isMatching, setIsMatching] = useState(false)
  const [error, setError] = useState(null)
  const [topK] = useState(15)

  const handleFileSelect = async (file) => {
    setError(null)
    setMatchResult(null)
    setIsUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await uploadResume(form)
      setResume(res.data)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Upload failed. Please try again.'
      setError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  const handleMatch = async () => {
    setError(null)
    setIsMatching(true)
    try {
      const res = await getResumeMatch(topK)
      setMatchResult(res.data)
    } catch (err) {
      const msg = err.response?.data?.detail || 'Matching failed. Please try again.'
      setError(msg)
    } finally {
      setIsMatching(false)
    }
  }

  const handleDelete = async () => {
    try {
      await deleteResume()
      setResume(null)
      setMatchResult(null)
    } catch (err) {
      setError('Could not delete resume.')
    }
  }

  return (
    <div id="career-ops" className="max-w-7xl mx-auto space-y-6">
      {/* Hero header */}
      <div
        className="rounded-2xl p-6 relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, rgba(37,99,235,0.15) 0%, rgba(124,58,237,0.15) 100%)', border: '1px solid rgba(99,102,241,0.2)' }}
      >
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)' }}>
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">CareerOps <span className="gradient-text">AI</span></h2>
              <p className="text-xs text-slate-400">Powered by LangChain RAG + Semantic Embeddings</p>
            </div>
          </div>
          <p className="text-slate-300 text-sm max-w-2xl">
            Upload your resume and let AI rank the best-matching jobs from our live database of 500+ positions across 5 job portals. Each match comes with a personalized explanation of why it fits.
          </p>
          <div className="flex flex-wrap gap-3 mt-4">
            {['📄 Resume Parsing', '🔍 Semantic Search', '🤖 AI Explanations', '⚡ Real-time Jobs'].map(tag => (
              <span key={tag} className="text-xs font-medium text-slate-300 bg-white/5 border border-white/10 rounded-full px-3 py-1">{tag}</span>
            ))}
          </div>
        </div>
        {/* Decorative gradient orbs */}
        <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full opacity-10 blur-3xl" style={{ background: 'radial-gradient(circle, #7c3aed, transparent)' }} />
        <div className="absolute -bottom-8 -left-8 w-32 h-32 rounded-full opacity-10 blur-3xl" style={{ background: 'radial-gradient(circle, #2563eb, transparent)' }} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-start gap-3 p-4 rounded-xl border border-red-500/30 bg-red-500/10">
          <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm text-red-300">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
            <X size={14} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panel — upload / resume */}
        <div className="lg:col-span-1 space-y-4">
          <div className="glass-card p-5">
            <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
              <FileText size={15} className="text-brand-400" /> Your Resume
            </h3>

            {!resume ? (
              <UploadZone onFileSelect={handleFileSelect} isUploading={isUploading} />
            ) : (
              <ResumeCard
                resume={resume}
                onDelete={handleDelete}
                onMatch={handleMatch}
                isMatching={isMatching}
              />
            )}
          </div>

          {/* How it works */}
          <div className="glass-card p-5">
            <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
              <TrendingUp size={15} className="text-purple-400" /> How It Works
            </h3>
            <ol className="space-y-3">
              {[
                { step: '1', label: 'Upload Resume', desc: 'PDF, DOCX, or TXT — AI extracts your skills and experience' },
                { step: '2', label: 'Semantic Search', desc: 'LangChain + FAISS embeds job descriptions and your resume' },
                { step: '3', label: 'AI Ranking', desc: 'Jobs ranked by similarity score with GPT-generated explanations' },
                { step: '4', label: 'Apply Directly', desc: 'One-click apply to matching jobs on their original portals' },
              ].map(({ step, label, desc }) => (
                <li key={step} className="flex gap-3">
                  <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                    style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)', color: 'white' }}>
                    {step}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-white">{label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* Right panel — results */}
        <div className="lg:col-span-2">
          {!matchResult && !isMatching && (
            <div className="glass-card p-12 text-center h-full flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 mx-auto"
                style={{ background: 'linear-gradient(135deg, rgba(37,99,235,0.2), rgba(124,58,237,0.2))' }}>
                <Sparkles className="w-7 h-7 text-brand-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Your AI Matches Appear Here</h3>
              <p className="text-slate-500 text-sm max-w-sm">
                Upload your resume and click "Find My Best Jobs" to see ranked matches with AI-powered explanations.
              </p>
            </div>
          )}

          {isMatching && (
            <div className="glass-card p-12 text-center">
              <Loader2 className="w-10 h-10 text-brand-400 animate-spin mx-auto mb-4" />
              <p className="text-white font-medium">Building semantic job index…</p>
              <p className="text-slate-500 text-sm mt-1">Running LangChain RAG pipeline across {500}+ jobs</p>
            </div>
          )}

          {matchResult && !isMatching && (
            <div className="space-y-4">
              {/* Results header */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white">
                    {matchResult.total} Best Matches Found
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1.5">
                    {matchResult.openai_powered ? (
                      <><Sparkles size={10} className="text-purple-400" /> GPT-3.5-turbo explanations</>
                    ) : (
                      <><Zap size={10} className="text-green-400" /> Keyword + semantic matching</>
                    )}
                  </p>
                </div>
                <button
                  onClick={handleMatch}
                  className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1 transition-colors"
                >
                  <Sparkles size={11} /> Re-match
                </button>
              </div>

              {/* Job cards */}
              <div id="match-results" className="space-y-3">
                {matchResult.jobs.map((job, i) => (
                  <MatchedJobCard
                    key={job.id}
                    job={job}
                    rank={i + 1}
                    openaiPowered={matchResult.openai_powered}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
