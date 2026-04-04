import { useEffect, useState, useCallback } from 'react'
import { Search, SlidersHorizontal, ChevronLeft, ChevronRight, X } from 'lucide-react'
import JobCard from '../components/JobCard'
import { fetchJobs, fetchCategories } from '../api/client'
import { useLocation } from 'react-router-dom'

const EXPERIENCE_LEVELS = ['Entry', 'Mid', 'Senior', 'Lead', 'Principal', 'Staff']
const REMOTE_TYPES = ['Remote', 'Hybrid', 'On-site']

export default function JobExplorer() {
  const location = useLocation()
  
  const [jobs, setJobs] = useState([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [page, setPage] = useState(1)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showFilters, setShowFilters] = useState(false)

  const initialSearch = new URLSearchParams(location.search).get('q') || ''

  const [filters, setFilters] = useState({
    search: initialSearch,
    category: '',
    remote: '',
    experience: '',
    min_salary: '',
  })

  // Sync when URL query changes (e.g. searching from Navbar while already on Jobs page)
  useEffect(() => {
    const q = new URLSearchParams(location.search).get('q')
    if (q !== null && q !== filters.search) {
      setFilters(prev => ({ ...prev, search: q }))
      setPage(1)
    }
  }, [location.search])

  const load = useCallback(() => {
    setLoading(true)
    const params = { page, limit: 12 }
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category
    if (filters.remote) params.remote = filters.remote
    if (filters.experience) params.experience = filters.experience
    if (filters.min_salary) params.min_salary = Number(filters.min_salary)

    fetchJobs(params)
      .then((r) => {
        setJobs(r.data.jobs)
        setTotal(r.data.total)
        setPages(r.data.pages)
      })
      .finally(() => setLoading(false))
  }, [page, filters])

  useEffect(() => { load() }, [load])
  useEffect(() => { fetchCategories().then(r => setCategories(r.data)) }, [])

  const setFilter = (k, v) => {
    setPage(1)
    setFilters(prev => ({ ...prev, [k]: v }))
  }

  const clearFilters = () => {
    setPage(1)
    setFilters({ search: '', category: '', remote: '', experience: '', min_salary: '' })
  }

  const activeCount = Object.values(filters).filter(Boolean).length

  return (
    <div id="job-explorer" className="space-y-5 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            Job <span className="gradient-text">Explorer</span>
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            {total.toLocaleString()} positions found
          </p>
        </div>
        <button
          id="toggle-filters"
          onClick={() => setShowFilters(p => !p)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200
                     border border-white/10 text-slate-300 hover:border-brand-500/50 hover:text-white"
        >
          <SlidersHorizontal size={15} />
          Filters
          {activeCount > 0 && (
            <span className="w-5 h-5 rounded-full bg-brand-500 text-white text-xs font-bold flex items-center justify-center">
              {activeCount}
            </span>
          )}
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
        <input
          id="job-search"
          type="text"
          placeholder="Search by title, company, or keyword…"
          value={filters.search}
          onChange={e => setFilter('search', e.target.value)}
          className="input-field pl-11 py-3 text-sm"
        />
        {filters.search && (
          <button onClick={() => setFilter('search', '')} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
            <X size={14} />
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="glass-card p-5 animate-slide-up">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-slate-500 font-medium mb-1.5 block">Category</label>
              <select
                id="filter-category"
                value={filters.category}
                onChange={e => setFilter('category', e.target.value)}
                className="input-field text-sm"
              >
                <option value="">All Categories</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 font-medium mb-1.5 block">Remote Type</label>
              <select
                id="filter-remote"
                value={filters.remote}
                onChange={e => setFilter('remote', e.target.value)}
                className="input-field text-sm"
              >
                <option value="">Any</option>
                {REMOTE_TYPES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 font-medium mb-1.5 block">Experience</label>
              <select
                id="filter-experience"
                value={filters.experience}
                onChange={e => setFilter('experience', e.target.value)}
                className="input-field text-sm"
              >
                <option value="">Any Level</option>
                {EXPERIENCE_LEVELS.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 font-medium mb-1.5 block">Min Salary ($)</label>
              <input
                id="filter-salary"
                type="number"
                placeholder="e.g. 100000"
                value={filters.min_salary}
                onChange={e => setFilter('min_salary', e.target.value)}
                className="input-field text-sm"
              />
            </div>
          </div>
          {activeCount > 0 && (
            <button
              id="clear-filters"
              onClick={clearFilters}
              className="mt-3 text-xs text-slate-500 hover:text-brand-400 transition-colors flex items-center gap-1"
            >
              <X size={12} /> Clear all filters
            </button>
          )}
        </div>
      )}

      {/* Job Grid */}
      {loading ? (
        <div id="jobs-loading" className="flex items-center justify-center h-64">
          <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <p className="text-2xl mb-2">🔍</p>
          <p className="text-slate-300 font-medium">No jobs match your filters</p>
          <p className="text-slate-500 text-sm mt-1">Try adjusting your search criteria</p>
        </div>
      ) : (
        <div id="jobs-grid" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {jobs.map((job, i) => <JobCard key={job.id} job={job} index={i} />)}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div id="pagination" className="flex items-center justify-center gap-2 pt-2">
          <button
            id="prev-page"
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
            className="p-2 rounded-xl border border-white/10 text-slate-400 hover:border-brand-500/50 hover:text-white
                       disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-sm text-slate-400 font-medium px-4">
            Page <span className="text-white">{page}</span> of <span className="text-white">{pages}</span>
          </span>
          <button
            id="next-page"
            disabled={page === pages}
            onClick={() => setPage(p => p + 1)}
            className="p-2 rounded-xl border border-white/10 text-slate-400 hover:border-brand-500/50 hover:text-white
                       disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  )
}
