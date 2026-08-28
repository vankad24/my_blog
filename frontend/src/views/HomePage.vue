<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import PostList from '@/components/PostList.vue'
import Pagination from '@/components/Pagination.vue'
import TagFilter from '@/components/TagFilter.vue'

const postsStore = usePostsStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const currentPage = ref(parseInt(route.query.page) || 1)
const searchQuery = ref(route.query.search || '')
const selectedTag = ref(route.query.tag || '')
const pageSize = 20

const totalPages = computed(() => Math.ceil(postsStore.pagination.count / pageSize))

onMounted(() => {
  loadPosts()
  postsStore.fetchTags()
})

let isExternalUpdate = false

watch([currentPage, searchQuery, selectedTag], () => {
  if (isExternalUpdate) return
  router.replace({
    query: {
      page: currentPage.value > 1 ? currentPage.value : undefined,
      search: searchQuery.value || undefined,
      tag: selectedTag.value || undefined,
    }
  })
  loadPosts()
})

// Обновляем ref при изменении query params (например, клик по тегу из PostCard)
watch(
  () => ({
    page: route.query.page,
    search: route.query.search,
    tag: route.query.tag,
  }),
  () => {
    isExternalUpdate = true
    currentPage.value = parseInt(route.query.page) || 1
    searchQuery.value = route.query.search || ''
    selectedTag.value = route.query.tag || ''
    loadPosts()
    nextTick(() => { isExternalUpdate = false })
  }
)

async function loadPosts() {
  loading.value = true
  try {
    await postsStore.fetchPosts({
      page: currentPage.value,
      search: searchQuery.value || undefined,
      tag: selectedTag.value || undefined,
    })
  } finally {
    loading.value = false
  }
}

function handlePageChange(page) {
  currentPage.value = page
}

async function handleLike(id) {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  const result = await postsStore.likePost(id)
  // Обновляем пост в списке
  const post = postsStore.posts.find(p => p.id === id)
  if (post) {
    post.is_liked = result.liked
    post.likes_count = result.likes_count
  }
}
</script>

<template>
  <div>
    <!-- Header -->

    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
      <div class="flex flex-wrap gap-4">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по заголовкам..."
            class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <!-- Tag filter -->
        <TagFilter v-model="selectedTag" />
      </div>
    </div>

    <!-- Posts -->
    <PostList
      :posts="postsStore.posts"
      :loading="loading"
      @like="handleLike"
    />

    <!-- Pagination -->
    <Pagination
      :current-page="currentPage"
      :total-pages="totalPages"
      @page-change="handlePageChange"
    />
  </div>
</template>