<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import PostList from '@/components/PostList.vue'
import Pagination from '@/components/Pagination.vue'

const postsStore = usePostsStore()
const authStore = useAuthStore()

const posts = ref([])
const loading = ref(true)
const currentPage = ref(1)
const pageSize = 20

const totalPages = computed(() => Math.ceil(posts.value.length / pageSize))

onMounted(async () => {
  try {
    const data = await postsStore.fetchLikedPosts()
    posts.value = Array.isArray(data) ? data : (data.results || [])
  } finally {
    loading.value = false
  }
})

async function handleLike(slug) {
  const result = await postsStore.likePost(slug)
  const post = posts.value.find(p => p.slug === slug)
  if (post) {
    post.is_liked = result.liked
    post.likes_count = result.likes_count
  }
  // Если лайк снят — убираем из избранного
  if (!result.liked) {
    posts.value = posts.value.filter(p => p.slug !== slug)
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Избранные посты</h1>

    <PostList
      :posts="posts"
      :loading="loading"
      @like="handleLike"
    />

    <div v-if="!loading && posts.length === 0" class="text-center py-12">
      <p class="text-gray-500 text-lg">Вы ещё не лайкнули ни одного поста</p>
      <router-link to="/" class="text-primary-600 hover:underline mt-2 inline-block">
        Перейти к постам →
      </router-link>
    </div>
  </div>
</template>