<script setup>
import PostCard from '@/components/PostCard.vue'
import Pagination from '@/components/Pagination.vue'

defineProps({
  posts: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['like', 'page-change'])
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
      @like="(slug) => emit('like', slug)"
    />
  </div>
</template>