import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API service functions
export const transactionService = {
  getAll: (params = {}) => api.get('/api/transactions', { params }),
  create: (data) => api.post('/api/transactions', data),
  getById: (id) => api.get(`/api/transactions/${id}`),
  delete: (id) => api.delete(`/api/transactions/${id}`),
  syncXero: () => api.post('/api/transactions/sync-xero'),
  getSummary: (params = {}) => api.get('/api/transactions/summary', { params }),
}

export const forecastService = {
  generate: (data) => api.post('/api/forecast', data),
  getAll: (params = {}) => api.get('/api/forecast', { params }),
  getLatest: (params = {}) => api.get('/api/forecast/latest', { params }),
  clear: (params = {}) => api.delete('/api/forecast', { params }),
}

export const simulationService = {
  run: (data) => api.post('/api/simulate', data),
  runBatch: (scenarios) => api.post('/api/simulate/batch', { scenarios }),
  getPresets: () => api.get('/api/simulate/presets'),
}

export const authService = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
  connectXero: () => api.get('/auth/xero/connect'),
  getXeroStatus: () => api.get('/auth/xero/status'),
  disconnectXero: () => api.post('/auth/xero/disconnect'),
}

export default api
