<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import PostCard from '@/components/PostCard.vue'
import Pagination from '@/components/Pagination.vue'

const authStore = useAuthStore()

const props = defineProps({
  posts: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['like', 'page-change', 'delete'])

const isAuthor = (post) => {
  return authStore.user?.login === post.author_login
}

function handleEdit(id) {
  window.location.href = `/edit/${id}`
}

function handleDelete(id) {
  emit('delete', id)
}
</script>

<template>
  <div v-if="loading" class="space-y-4">
    <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-pulse">
      <div class="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
      <div class="h-6 bg-gray-200 rounded w-3/4 mb-3"></div>
      <div class="h-4 bg-gray-200 rounded w-full mb-2"></div>
      <div class="h-4 bg-gray-200 rounded w-2/3"></div>
    </div>
  </div>
  <div v-else-if="posts.length === 0" class="text-center py-12">
    <p class="text-gray-500 text-lg">Постов пока нет</p>
  </div>
  <div v-else class="space-y-6">
    <PostCard
      v-for="post in posts"
      :key="post.id"
      :post="post"
      :is-author="isAuthor(post)"
      :on-edit="handleEdit"
      :on-delete="handleDelete"
      @like="(id) => emit('like', id)"
    />
  </div>
</template>