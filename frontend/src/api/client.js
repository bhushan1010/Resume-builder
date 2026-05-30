import axios from 'axios';

const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const api = axios.create({ baseURL: BASE_URL });

// Request interceptor to attach JWT token and optional custom Gemini API Key
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Attach custom Gemini API key if selected provider is personal_gemini
    const provider = localStorage.getItem('llm_provider');
    const personalKey = localStorage.getItem('personal_gemini_key');
    if (provider === 'personal_gemini' && personalKey) {
      config.headers['X-Personal-Gemini-Key'] = personalKey;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;