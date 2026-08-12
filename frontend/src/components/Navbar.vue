<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const isLoggedIn = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.user)
const isModerator = computed(() => authStore.isModerator)

function handleLogout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <nav class="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
    <div class="max-w-5xl mx-auto px-4">
      <div class="flex justify-between items-center h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center space-x-2">
          <span class="text-2xl font-bold text-primary-600">MyBlog</span>
        </router-link>

        <!-- Navigation -->
        <div class="flex items-center space-x-4">
          <router-link to="/" class="nav-link" :class="{ 'text-primary-600': route.name === 'Home' }">
            Главная
          </router-link>

          <template v-if="isLoggedIn">
            <router-link to="/create" class="nav-link" :class="{ 'text-primary-600': route.name === 'CreatePost' }">
              Написать
            </router-link>
            <router-link to="/liked" class="nav-link" :class="{ 'text-primary-600': route.name === 'LikedPosts' }">
              Избранное
            </router-link>
            <router-link
              v-if="isModerator"
              to="/moderation"
              class="nav-link"
              :class="{ 'text-primary-600': route.name === 'Moderation' }"
            >
              Модерация
            </router-link>
            <router-link
              v-if="currentUser"
              :to="{ name: 'Profile', params: { login: currentUser.login } }"
              class="nav-link"
              :class="{ 'text-primary-600': route.name === 'Profile' }"
            >
              Профиль
            </router-link>
            <button
              @click="handleLogout"
              class="btn-secondary text-sm"
            >
              Выйти
            </button>
          </template>
          <template v-else>
            <router-link to="/login" class="btn-secondary text-sm">Войти</router-link>
            <router-link to="/register" class="btn-primary text-sm">Регистрация</router-link>
          </template>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.nav-link {
  @apply text-gray-600 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium transition-colors;
}
.btn-primary {
  @apply bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors font-medium;
}
.btn-secondary {
  @apply text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors font-medium;
}
</style>