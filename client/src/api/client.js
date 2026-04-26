import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60s for AI matching which can take time
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token automatically to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
})

// Auto-redirect to login on 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const path = window.location.pathname;
      if (path !== '/login') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
)

// ── Job endpoints ──────────────────────────────────────────────────────────
export const fetchJobs = (params = {}) => api.get('/jobs', { params })
export const fetchJob = (id) => api.get(`/jobs/${id}`)
export const fetchSummary = () => api.get('/stats/summary')
export const fetchSkillStats = () => api.get('/stats/skills')
export const fetchSalaryStats = () => api.get('/stats/salary')
export const fetchTrends = () => api.get('/stats/trends')
export const fetchCategories = () => api.get('/categories')
export const fetchSources = () => api.get('/sources')
export const triggerScrape = () => api.post('/scrape')

// ── Resume / AI endpoints ──────────────────────────────────────────────────
export const uploadResume = (formData) =>
  api.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

export const getMyResume = () => api.get('/resume/me')
export const deleteResume = () => api.delete('/resume/me')
export const getResumeMatch = (topK = 15) =>
  api.post(`/resume/match?top_k=${topK}`)

export default api
