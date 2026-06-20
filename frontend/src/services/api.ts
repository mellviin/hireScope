import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle expired/invalid tokens
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
export const authAPI = {
  signup: (data: any) => api.post('/auth/signup', data),
  login: (data: any) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
};

// Resume API
export const resumeAPI = {
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/resume/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  listResumes: () => api.get('/resume/list'),
  getResume: (id: number) => api.get(`/resume/${id}`),
  deleteResume: (id: number) => api.delete(`/resume/${id}`),
};

// Job Description API
export const jdAPI = {
  analyzeJD: (data: any) => api.post('/jd/analyze', data),
  listJDs: () => api.get('/jd/list'),
  getJD: (id: number) => api.get(`/jd/${id}`),
  deleteJD: (id: number) => api.delete(`/jd/${id}`),
};

// Analysis API
export const analysisAPI = {
  calculateMatch: (data: any) => api.post('/analysis/match', data),
  getGapAnalysis: (data: any) => api.post('/analysis/gap-analysis', data),
  getOptimizations: (data: any) => api.post('/analysis/optimize', data),
  getHistory: () => api.get('/analysis/history'),
  downloadReport: (data: { resume_id: number; job_description_id: number }) =>
    api.post('/analysis/report/download', data, { responseType: 'blob' }),
};

export default api;
