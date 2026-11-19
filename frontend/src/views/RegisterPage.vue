<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const form = ref({
  login: '',
  email: '',
  name: '',
  password: '',
  password_confirm: '',
})
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  if (form.value.password !== form.value.password_confirm) {
    error.value = 'Пароли не совпадают'
    return
  }
  if (form.value.password.length < 8) {
    error.value = 'Пароль должен содержать минимум 8 символов'
    return
  }

  loading.value = true
  try {
    const data = await authStore.register(
      form.value.login,
      form.value.email,
      form.value.name,
      form.value.password,
      form.value.password_confirm
    )
    // Регистрация требует подтверждения модератора — вход не выполняем
    success.value = data?.message || 'Ожидайте подтверждения регистрации'
  } catch (err) {
    if (err.response?.status === 429) {
      error.value = err.response.data?.detail || 'Слишком много попыток, попробуйте позже'
    } else if (err.response?.data) {
      const errors = err.response.data
      error.value = Object.entries(errors)
        .map(([k, v]) => Array.isArray(v) ? v.join(', ') : v)
        .join('; ')
    } else {
      error.value = 'Ошибка регистрации'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-md mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6 text-center">Регистрация</h1>

    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4">
      {{ error }}
    </div>

    <div
      v-if="success"
      class="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-6 text-center"
    >
      <p class="text-lg font-medium">{{ success }}</p>
      <p class="text-sm text-yellow-700 mt-2">
        Доступ к аккаунту появится после подтверждения модератором.
      </p>
      <router-link
        to="/login"
        class="inline-block mt-4 text-primary-600 hover:underline text-sm"
      >
        Перейти к входу
      </router-link>
    </div>

    <form
      v-else
      @submit.prevent="handleSubmit"
      class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4"
    >
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Логин</label>
        <input
          v-model="form.login"
          type="text"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="Ваш логин"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
        <input
          v-model="form.email"
          type="email"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="email@example.com"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Имя</label>
        <input
          v-model="form.name"
          type="text"
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="Ваше имя"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Пароль</label>
        <input
          v-model="form.password"
          type="password"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="Минимум 8 символов"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Подтверждение пароля</label>
        <input
          v-model="form.password_confirm"
          type="password"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="Повторите пароль"
        />
      </div>

      <button
        type="submit"
        :disabled="loading"
        class="w-full bg-primary-600 text-white py-2.5 rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:opacity-50"
      >
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>
    </form>

    <p class="text-center text-gray-500 text-sm mt-4">
      Уже есть аккаунт?
      <router-link to="/login" class="text-primary-600 hover:underline">Войти</router-link>
    </p>
  </div>
</template>