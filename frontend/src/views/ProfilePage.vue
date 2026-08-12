<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const profile = ref(null)
const userPosts = ref([])
const loading = ref(true)
const editMode = ref(false)
const editForm = ref({ name: '', email: '' })
const passwordForm = ref({ old_password: '', new_password: '', new_password_confirm: '' })
const message = ref('')
const error = ref('')

const isOwnProfile = computed(() => {
  if (!authStore.user) return false
  return authStore.user.login === route.params.login
})

onMounted(async () => {
  loading.value = true
  try {
    const { data } = await apiClient.get(`/users/${route.params.login}/`)
    profile.value = data
    editForm.value = { name: data.name, email: data.email }
  } catch {
    profile.value = null
  } finally {
    loading.value = false
  }
})

async function updateProfile() {
  error.value = ''
  message.value = ''
  try {
    await authStore.updateProfile(editForm.value)
    profile.value = { ...profile.value, ...editForm.value }
    message.value = 'Профиль обновлён'
    editMode.value = false
  } catch (err) {
    error.value = 'Ошибка обновления профиля'
  }
}

async function changePassword() {
  error.value = ''
  message.value = ''
  if (passwordForm.value.new_password !== passwordForm.value.new_password_confirm) {
    error.value = 'Новые пароли не совпадают'
    return
  }
  try {
    await authStore.changePassword(
      passwordForm.value.old_password,
      passwordForm.value.new_password,
      passwordForm.value.new_password_confirm
    )
    message.value = 'Пароль изменён'
    passwordForm.value = { old_password: '', new_password: '', new_password_confirm: '' }
  } catch (err) {
    error.value = 'Ошибка смены пароля'
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto">
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-gray-200 rounded w-1/3"></div>
      <div class="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>

    <div v-else-if="profile">
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div class="flex items-center space-x-4 mb-6">
          <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            <span class="text-2xl font-bold text-primary-600">
              {{ (profile.name || profile.login)[0].toUpperCase() }}
            </span>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">{{ profile.name || profile.login }}</h1>
            <p class="text-gray-500">@{{ profile.login }}</p>
          </div>
        </div>

        <div class="flex space-x-4 text-sm text-gray-500">
          <span>Роль: {{ profile.role === 'admin' ? 'Администратор' : profile.role === 'moderator' ? 'Модератор' : 'Пользователь' }}</span>
          <span>Зарегистрирован: {{ new Date(profile.created_at).toLocaleDateString('ru-RU') }}</span>
        </div>

        <!-- Edit Profile -->
        <template v-if="isOwnProfile">
          <div v-if="message" class="bg-green-50 border border-green-200 text-green-700 rounded-lg p-4 mt-4">
            {{ message }}
          </div>
          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mt-4">
            {{ error }}
          </div>

          <button
            v-if="!editMode"
            @click="editMode = true"
            class="mt-4 text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            Редактировать профиль
          </button>

          <div v-if="editMode" class="mt-4 space-y-4 border-t border-gray-100 pt-4">
            <h3 class="font-medium text-gray-900">Редактирование профиля</h3>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Имя</label>
              <input
                v-model="editForm.name"
                type="text"
                class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                v-model="editForm.email"
                type="email"
                class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            <div class="flex space-x-2">
              <button @click="updateProfile" class="btn-primary">Сохранить</button>
              <button @click="editMode = false" class="btn-secondary">Отмена</button>
            </div>
          </div>

          <!-- Change Password -->
          <div class="mt-6 border-t border-gray-100 pt-4">
            <h3 class="font-medium text-gray-900 mb-4">Смена пароля</h3>
            <form @submit.prevent="changePassword" class="space-y-3 max-w-md">
              <input
                v-model="passwordForm.old_password"
                type="password"
                placeholder="Текущий пароль"
                class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="Новый пароль"
                class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <input
                v-model="passwordForm.new_password_confirm"
                type="password"
                placeholder="Подтвердите новый пароль"
                class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button type="submit" class="btn-primary">Сменить пароль</button>
            </form>
          </div>
        </template>
      </div>
    </div>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 text-lg">Пользователь не найден</p>
    </div>
  </div>
</template>

<style scoped>
.btn-primary {
  @apply bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm;
}
.btn-secondary {
  @apply text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors font-medium text-sm;
}
</style>