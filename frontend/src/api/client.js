import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Эндпоинты, для которых не нужно обновлять токен и повторять запрос
const AUTH_PATHS = ['/auth/login/', '/auth/register/', '/auth/refresh/', '/auth/guest/']

function isAuthRequest(url = '') {
  return AUTH_PATHS.some((path) => url.includes(path))
}

// Request interceptor — Bearer для авторизованного, Guest для гостя
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    } else if (authStore.guestToken) {
      config.headers.Authorization = `Guest ${authStore.guestToken}`
    } else {
      delete config.headers.Authorization
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — обновление токена и откат к гостевому токену
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (!originalRequest) return Promise.reject(error)

    const shouldRefresh =
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isAuthRequest(originalRequest.url)

    if (!shouldRefresh) return Promise.reject(error)

    originalRequest._retry = true
    const authStore = useAuthStore()

    if (!authStore.refreshToken && !authStore.accessToken) {
      return Promise.reject(error)
    }

    if (authStore.refreshToken) {
      try {
        const { data } = await axios.post('/api/auth/refresh/', {
          refresh: authStore.refreshToken,
        })
        authStore.setTokens(data.access, data.refresh)
        originalRequest.headers = originalRequest.headers || {}
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return apiClient(originalRequest)
      } catch {
        // Refresh не сработал — сессия отозвана или истекла
      }
    }

    // Продолжаем как гость: публичные запросы должны работать
    authStore.clearTokens()
    authStore.user = null
    await authStore.ensureGuestToken()
    originalRequest.headers = originalRequest.headers || {}
    delete originalRequest.headers.Authorization
    return apiClient(originalRequest)
  }
)

export default apiClient
