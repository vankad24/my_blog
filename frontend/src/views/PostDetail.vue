<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import CommentForm from '@/components/CommentForm.vue'
import PostCard from '@/components/PostCard.vue'
import MarkdownPreview from '@/components/MarkdownPreview.vue'
import { formatRelativeDate } from '@/utils/formatDate'

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
  await postsStore.deletePost(post.value.id)
  router.push('/')
}

async function handleComment(data) {
  data.object_id = post.value.id
  await postsStore.createComment(data)
  await loadComments()
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

function formatDate(dateStr) {
  return formatRelativeDate(dateStr)
}
</script>

<template>
  <div>
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-gray-200 rounded w-3/4"></div>
      <div class="h-4 bg-gray-200 rounded w-1/4"></div>
      <div class="h-64 bg-gray-200 rounded"></div>
    </div>

    <div v-else-if="post">
      <!-- Post Card -->
      <PostCard
        :post="post"
        :is-author="isAuthor"
        :on-edit="(id) => router.push({ name: 'EditPost', params: { id } })"
        :on-delete="handleDelete"
        @like="handleLike"
      />

      <!-- Comments Section -->
      <div class="border-t border-gray-100 p-8 mt-6">
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