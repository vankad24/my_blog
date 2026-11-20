<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '@/api/client'

const route = useRoute()
const totalVisits = ref(null)
let requestSeq = 0

async function registerVisit() {
  const seq = ++requestSeq
  try {
    const { data } = await apiClient.post('/visits/')
    if (seq === requestSeq && typeof data.total === 'number') {
      totalVisits.value = data.total
    }
  } catch {
    // Счётчик посещений не критичен для работы сайта
  }
}

onMounted(registerVisit)
watch(() => route.path, registerVisit)
</script>

<template>
  <footer class="bg-white border-t border-gray-200 mt-32">
    <div class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-gray-500 text-sm">&copy; {{ new Date().getFullYear() }} Molo4ko production. Все права не защищены.</p>
        <div class="flex flex-col items-center gap-3 sm:flex-row sm:gap-6">
          <div class="flex space-x-4">
            <router-link to="/privacy" class="text-gray-400 hover:text-gray-600 text-sm">Политика конфиденциальности</router-link>
            <router-link to="/terms" class="text-gray-400 hover:text-gray-600 text-sm">Условия использования</router-link>
          </div>
          <span
            v-if="totalVisits !== null"
            class="flex items-center space-x-1 text-gray-500 text-sm sm:border-l sm:border-gray-200 sm:pl-6"
            title="Всего посещений"
            aria-label="Всего посещений"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span>{{ totalVisits.toLocaleString('ru-RU') }}</span>
          </span>
        </div>
      </div>
    </div>
  </footer>
</template>
