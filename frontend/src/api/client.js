import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — добавляем JWT токен
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — обработка 401 и обновление токена
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const authStore = useAuthStore()
      if (authStore.refreshToken) {
        try {
          const { data } = await axios.post('/api/auth/refresh/', {
            refresh: authStore.refreshToken,
          })
          authStore.setTokens(data.access, data.refresh)
          originalRequest.headers.Authorization = `Bearer ${data.access}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          authStore.logout()
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient