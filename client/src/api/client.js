import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token automatically
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
})

export const fetchJobs = (params = {}) => api.get('/jobs', { params })
export const fetchJob = (id) => api.get(`/jobs/${id}`)
export const fetchSummary = () => api.get('/stats/summary')
export const fetchSkillStats = () => api.get('/stats/skills')
export const fetchSalaryStats = () => api.get('/stats/salary')
export const fetchTrends = () => api.get('/stats/trends')
export const fetchCategories = () => api.get('/categories')

export default api
