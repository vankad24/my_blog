<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import TagChip from '@/components/TagChip.vue'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['like'])
const authStore = useAuthStore()

const authorName = computed(() => props.post.author_name || props.post.author?.name || props.post.author_login)
const authorLogin = computed(() => props.post.author_login || props.post.author?.login)
const isLiked = computed(() => props.post.is_liked)
const likesCount = computed(() => props.post.likes_count)

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function handleLike() {
  if (authStore.isAuthenticated) {
    emit('like', props.post.id)
  }
}
</script>

<template>
  <article class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
    <div class="p-6">
      <!-- Status badge -->
      <div class="mb-3">
        <span
          v-if="post.status === 'draft'"
          class="inline-block bg-yellow-50 text-yellow-700 text-xs font-medium px-2.5 py-1 rounded-full"
        >
          Черновик
        </span>
        <span
          v-else-if="post.status === 'moderation'"
          class="inline-block bg-orange-50 text-orange-700 text-xs font-medium px-2.5 py-1 rounded-full"
        >
          На модерации
        </span>
      </div>

      <!-- Content preview -->
      <router-link :to="{ name: 'PostDetail', params: { id: post.id } }" class="block mb-4">
        <MarkdownPreview :markdown="post.content" />
      </router-link>

      <!-- Tags -->
      <div v-if="post.tags?.length" class="flex flex-wrap gap-2 mb-4">
        <TagChip
          v-for="tag in post.tags"
          :key="tag.id"
          :name="tag.name"
          :to="{ name: 'Home', query: { tag: tag.id } }"
        />
      </div>

      <!-- Meta -->
      <div class="flex items-center justify-between text-sm text-gray-500">
        <div class="flex items-center space-x-4">
          <router-link
            :to="{ name: 'Profile', params: { login: authorLogin } }"
            class="hover:text-primary-600"
          >
            {{ authorName }}
          </router-link>
          <span>{{ formatDate(post.published_at || post.created_at) }}</span>
        </div>
        <div class="flex items-center space-x-3">
          <span class="flex items-center space-x-1">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span>{{ post.views || 0 }}</span>
          </span>
          <button
            @click="handleLike"
            class="flex items-center space-x-1 transition-colors"
            :class="isLiked ? 'text-red-500' : 'hover:text-red-500'"
          >
            <svg
              class="w-4 h-4"
              :fill="isLiked ? 'currentColor' : 'none'"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
            <span>{{ likesCount || 0 }}</span>
          </button>
        </div>
      </div>
    </div>
  </article>
</template>