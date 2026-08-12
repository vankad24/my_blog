import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import { useRouter } from 'vue-router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isModerator = computed(() => user.value?.role === 'moderator' || user.value?.role === 'admin')
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('accessToken', access)
    localStorage.setItem('refreshToken', refresh)
  }

  function clearTokens() {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  }

  async function fetchUser() {
    try {
      const { data } = await apiClient.get('/me/')
      user.value = data
      return data
    } catch (error) {
      clearTokens()
      user.value = null
      throw error
    }
  }

  async function login(login, password) {
    const { data } = await apiClient.post('/auth/login/', { login, password })
    setTokens(data.access, data.refresh)
    await fetchUser()
    return data
  }

  async function register(login, email, name, password, passwordConfirm) {
    const { data } = await apiClient.post('/auth/register/', {
      login,
      email,
      name,
      password,
      password_confirm: passwordConfirm,
    })
    return data
  }

  async function logout() {
    try {
      if (refreshToken.value) {
        await apiClient.post('/auth/logout/', { refresh: refreshToken.value })
      }
    } catch (e) {
      // Игнорируем ошибки выхода
    }
    clearTokens()
    user.value = null
  }

  async function updateProfile(data) {
    const { data: result } = await apiClient.patch('/me/update/', data)
    user.value = { ...user.value, ...result }
    return result
  }

  async function changePassword(oldPassword, newPassword, newPasswordConfirm) {
    await apiClient.post('/me/password/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    })
  }

  async function requestPasswordReset(email) {
    const { data } = await apiClient.post('/auth/password/reset/request/', { email })
    return data
  }

  async function confirmPasswordReset(uid, token, newPassword, newPasswordConfirm) {
    await apiClient.post('/auth/password/reset/confirm/', {
      uid,
      token,
      new_password: newPassword,
      new_password_confirm: newPasswordConfirm,
    })
  }

  async function verifyEmail(uid, token) {
    await apiClient.post('/auth/email/verify/', { uid, token })
  }

  // Инициализация — проверяем токен при загрузке
  async function init() {
    if (accessToken.value) {
      try {
        await fetchUser()
      } catch {
        clearTokens()
      }
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    isModerator,
    isAdmin,
    setTokens,
    clearTokens,
    fetchUser,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    confirmPasswordReset,
    verifyEmail,
    init,
  }
})