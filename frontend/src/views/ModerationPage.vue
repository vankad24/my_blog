<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

const authStore = useAuthStore()
const items = ref([])
const loading = ref(true)
const filterStatus = ref('pending')

onMounted(() => {
  loadModeration()
})

async function loadModeration() {
  loading.value = true
  try {
    const { data } = await apiClient.get('/moderation/', {
      params: { status: filterStatus.value },
    })
    items.value = data.results || data
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function accept(id) {
  const comment = prompt('Комментарий модератора (необязательно):') || ''
  try {
    await apiClient.post(`/moderation/${id}/accept/`, { comment })
    items.value = items.value.filter(i => i.id !== id)
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || 'не удалось'))
  }
}

async function decline(id) {
  const comment = prompt('Причина отклонения:') || ''
  try {
    await apiClient.post(`/moderation/${id}/decline/`, { comment })
    items.value = items.value.filter(i => i.id !== id)
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || 'не удалось'))
  }
}

function changeStatus(status) {
  filterStatus.value = status
  loadModeration()
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Панель модерации</h1>

    <!-- Status tabs -->
    <div class="flex space-x-2 mb-6">
      <button
        v-for="s in [
          { value: 'pending', label: 'Ожидают' },
          { value: 'accepted', label: 'Принятые' },
          { value: 'declined', label: 'Отклонённые' },
        ]"
        :key="s.value"
        @click="changeStatus(s.value)"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="filterStatus === s.value
          ? 'bg-primary-600 text-white'
          : 'bg-white border border-gray-300 hover:bg-gray-50'"
      >
        {{ s.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-pulse">
        <div class="h-4 bg-gray-200 rounded w-1/4 mb-3"></div>
        <div class="h-6 bg-gray-200 rounded w-3/4"></div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else-if="items.length === 0" class="text-center py-12">
      <p class="text-gray-500 text-lg">Нет объектов на модерации</p>
    </div>

    <!-- List -->
    <div v-else class="space-y-4">
      <div
        v-for="item in items"
        :key="item.id"
        class="bg-white rounded-xl shadow-sm border border-gray-100 p-6"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <!-- Content info -->
            <div class="flex items-center space-x-2 mb-2">
              <span class="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded">
                {{ item.content_type_name === 'post' ? 'Пост' : 'Комментарий' }}
              </span>
              <span
                class="text-xs font-medium px-2 py-1 rounded"
                :class="{
                  'bg-yellow-50 text-yellow-700': item.status === 'pending',
                  'bg-green-50 text-green-700': item.status === 'accepted',
                  'bg-red-50 text-red-700': item.status === 'declined',
                }"
              >
                {{ item.status === 'pending' ? 'Ожидает' : item.status === 'accepted' ? 'Принят' : 'Отклонён' }}
              </span>
            </div>

            <!-- Content -->
            <div v-if="item.content_object">
              <h3 v-if="item.content_object.title" class="text-lg font-semibold text-gray-900">
                {{ item.content_object.title }}
              </h3>
              <p v-if="item.content_object.body" class="text-gray-600 text-sm">
                {{ item.content_object.body }}
              </p>
            </div>

            <!-- Moderator comment -->
            <p v-if="item.comment" class="text-sm text-gray-500 mt-2 italic">
              Модератор: {{ item.comment }}
            </p>
          </div>

          <!-- Actions -->
          <div v-if="item.status === 'pending'" class="flex space-x-2 ml-4">
            <button
              @click="accept(item.id)"
              class="bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
            >
              Принять
            </button>
            <button
              @click="decline(item.id)"
              class="bg-red-600 text-white px-3 py-1.5 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
            >
              Отклонить
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>