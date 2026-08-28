<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import CommentForm from '@/components/CommentForm.vue'
import MarkdownPreview from '@/components/MarkdownPreview.vue'

const route = useRoute()
const router = useRouter()
const postsStore = usePostsStore()
const authStore = useAuthStore()

const loading = ref(true)
const comments = ref([])
const liked = ref(false)
const post = ref(null)
const showCopied = ref(false)

const isAuthor = computed(() => {
  if (!authStore.user || !post.value) return false
  return authStore.user.login === post.value.author_login
})

onMounted(async () => {
  try {
    await postsStore.fetchPost(route.params.id)
    post.value = postsStore.currentPost
    liked.value = post.value.is_liked || false
    await loadComments()
  } finally {
    loading.value = false
  }
})

async function loadComments() {
  try {
    const data = await postsStore.fetchComments(post.value.id)
    comments.value = data
  } catch (e) {
    comments.value = []
  }
}

async function handleLike() {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  const result = await postsStore.likePost(post.value.id)
  post.value.likes_count = result.likes_count
  liked.value = result.liked
}

async function handleDelete() {
  if (!confirm('Удалить пост?')) return
  await postsStore.deletePost(post.value.id)
  router.push('/')
}

async function handleComment(data) {
  data.object_id = post.value.id
  await postsStore.createComment(data)
  await loadComments()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function sharePost() {
  try {
    await navigator.clipboard.writeText(window.location.href)
  } catch {
    const input = document.createElement('input')
    input.value = window.location.href
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
  }
  showCopied.value = true
  setTimeout(() => { showCopied.value = false }, 2000)
}
</script>

<template>
  <div>
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-gray-200 rounded w-3/4"></div>
      <div class="h-4 bg-gray-200 rounded w-1/4"></div>
      <div class="h-64 bg-gray-200 rounded"></div>
    </div>

    <div v-else-if="post" class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <!-- Post Header -->
      <div class="p-8">
        <!-- Status badge -->
        <div class="mb-4">
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

        <h1 class="text-3xl font-bold text-gray-900 mb-4">{{ post.title }}</h1>

        <!-- Author & Meta -->
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center space-x-4 text-sm text-gray-500">
            <router-link
              :to="{ name: 'Profile', params: { login: post.author.login } }"
              class="font-medium hover:text-primary-600"
            >
              {{ post.author.name || post.author.login }}
            </router-link>
            <span>{{ formatDate(post.published_at || post.created_at) }}</span>
            <span class="flex items-center space-x-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <span>{{ post.views || 0 }}</span>
            </span>
          </div>

          <!-- Actions -->
          <div class="flex items-center space-x-2">
            <button
              @click="handleLike"
              class="flex items-center space-x-1 px-3 py-1.5 rounded-lg transition-colors relative group"
              :class="liked ? 'bg-red-50 text-red-500' : 'hover:bg-gray-100'"
            >
              <svg
                class="w-5 h-5"
                :fill="liked ? 'currentColor' : 'none'"
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
              <span>{{ post.likes_count || 0 }}</span>
              <span class="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                Лайк
              </span>
            </button>

            <router-link
              v-if="isAuthor"
              :to="{ name: 'EditPost', params: { id: post.id } }"
              class="text-gray-500 hover:text-primary-600 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition-colors text-sm"
            >
              Редактировать
            </router-link>
            <button
              v-if="isAuthor"
              @click="handleDelete"
              class="text-red-500 hover:text-red-600 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors text-sm"
            >
              Удалить
            </button>

            <!-- Share -->
            <div class="relative group">
              <button
                @click="sharePost"
                class="text-gray-500 hover:text-primary-600 px-2 py-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
              </button>
              <span class="absolute -top-8 right-0 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                Поделиться
              </span>
              <span
                v-show="showCopied"
                class="absolute -top-8 right-0 px-2 py-1 bg-primary-600 text-white text-xs rounded whitespace-nowrap"
              >
                Скопировано!
              </span>
            </div>
          </div>
        </div>

        <!-- Tags -->
        <div v-if="post.tags?.length" class="flex flex-wrap gap-2 mb-6">
          <span
            v-for="tag in post.tags"
            :key="tag.id"
            class="text-sm text-gray-500 bg-gray-100 px-2.5 py-1 rounded"
          >
            #{{ tag.name }}
          </span>
        </div>

        <!-- Content -->
        <div class="prose-content">
          <MarkdownPreview :markdown="post.content" />
        </div>
      </div>

      <!-- Comments Section -->
      <div class="border-t border-gray-100 p-8">
        <h2 class="text-xl font-bold text-gray-900 mb-6">
          Комментарии
          <span v-if="comments.length" class="text-gray-500 text-base font-normal">({{ comments.length }})</span>
        </h2>

        <CommentForm :post-id="post.id" @submitted="handleComment" />

        <div class="mt-6 space-y-4">
          <div v-for="comment in comments" :key="comment.id" class="bg-gray-50 rounded-lg p-4">
            <div class="flex items-center space-x-2 text-sm text-gray-500 mb-2">
              <span class="font-medium text-gray-900">{{ comment.author_name || comment.author_login }}</span>
              <span>{{ formatDate(comment.created_at) }}</span>
            </div>
            <div class="text-gray-700">
              <MarkdownPreview :markdown="comment.body" />
            </div>

            <!-- Replies -->
            <div v-if="comment.replies?.length" class="ml-6 mt-4 space-y-3">
              <div v-for="reply in comment.replies" :key="reply.id" class="bg-white rounded-lg p-3 border border-gray-200">
                <div class="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                  <span class="font-medium text-gray-900">{{ reply.author_name || reply.author_login }}</span>
                  <span>{{ formatDate(reply.created_at) }}</span>
                </div>
                <div class="text-gray-700">
                  <MarkdownPreview :markdown="reply.body" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 text-lg">Пост не найден</p>
      <router-link to="/" class="text-primary-600 hover:underline mt-2 inline-block">Вернуться на главную</router-link>
    </div>
  </div>
</template>