<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import { useAuthStore } from '@/stores/auth'
import PostList from '@/components/PostList.vue'
import TagFilter from '@/components/TagFilter.vue'

const postsStore = usePostsStore()
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const SEARCH_DEBOUNCE = 300
// Подгружаем чуть раньше, чем пользователь доскроллит до самого низа
const SCROLL_THRESHOLD = 200

const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const searchQuery = ref(route.query.search || '')
const selectedTag = ref(route.query.tag || '')

const loadMoreTrigger = ref(null)

const hasMore = computed(() => Boolean(postsStore.pagination.next))
const allLoaded = computed(
  () => !loading.value && !loadingMore.value && !hasMore.value && postsStore.posts.length > 0
)

let isExternalUpdate = false
let searchTimer = null
let observer = null
// Номер запроса защищает от гонок при быстрой смене фильтров
let requestSeq = 0

onMounted(async () => {
  await loadFirstPage()
  postsStore.fetchTags()
  await nextTick()
  setupObserver()
})

onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
  if (observer) observer.disconnect()
})

watch(searchQuery, () => {
  if (isExternalUpdate) return
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    syncQuery()
    loadFirstPage()
  }, SEARCH_DEBOUNCE)
})

watch(selectedTag, () => {
  if (isExternalUpdate) return
  if (searchTimer) clearTimeout(searchTimer)
  syncQuery()
  loadFirstPage()
})

// Обновляем ref при изменении query params (например, клик по тегу из PostCard)
watch(
  () => ({
    search: route.query.search,
    tag: route.query.tag,
  }),
  (query) => {
    const nextSearch = query.search || ''
    const nextTag = query.tag || ''
    // TagFilter отдаёт id числом, а route.query — строкой
    if (
      String(nextSearch) === String(searchQuery.value) &&
      String(nextTag) === String(selectedTag.value)
    ) {
      return
    }

    if (searchTimer) clearTimeout(searchTimer)
    isExternalUpdate = true
    searchQuery.value = nextSearch
    selectedTag.value = nextTag
    loadFirstPage()
    nextTick(() => { isExternalUpdate = false })
  }
)

function syncQuery() {
  router.replace({
    query: {
      search: searchQuery.value || undefined,
      tag: selectedTag.value || undefined,
    },
  })
}

async function loadFirstPage() {
  const seq = ++requestSeq
  loading.value = true
  loadingMore.value = false
  page.value = 1

  try {
    await postsStore.fetchPosts(
      {
        page: 1,
        search: searchQuery.value || undefined,
        tag: selectedTag.value || undefined,
      },
      {
        append: false,
        shouldApply: () => seq === requestSeq,
      }
    )
  } catch {
    // Не удалось загрузить — оставляем текущий список
  } finally {
    if (seq === requestSeq) loading.value = false
  }

  if (seq !== requestSeq) return
  await nextTick()
  autoLoadIfNeeded()
}

async function loadMore() {
  if (loading.value || loadingMore.value || !hasMore.value) return

  const seq = requestSeq
  const nextPage = page.value + 1
  loadingMore.value = true
  let loaded = false

  try {
    await postsStore.fetchPosts(
      {
        page: nextPage,
        search: searchQuery.value || undefined,
        tag: selectedTag.value || undefined,
      },
      {
        append: true,
        shouldApply: () => seq === requestSeq,
      }
    )
    loaded = seq === requestSeq
    if (loaded) page.value = nextPage
  } catch {
    // Страницу не сдвигаем — повторим при следующем скролле
  } finally {
    if (seq === requestSeq) loadingMore.value = false
  }

  if (!loaded) return
  await nextTick()
  autoLoadIfNeeded()
}

function setupObserver() {
  if (observer || !loadMoreTrigger.value) return
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) loadMore()
    },
    { rootMargin: `${SCROLL_THRESHOLD}px 0px`, threshold: 0 }
  )
  observer.observe(loadMoreTrigger.value)
}

// Если порция не заполнила экран, догружаем следующую без скролла
function autoLoadIfNeeded() {
  if (!hasMore.value || !loadMoreTrigger.value) return
  const rect = loadMoreTrigger.value.getBoundingClientRect()
  if (rect.top <= window.innerHeight + SCROLL_THRESHOLD) {
    loadMore()
  }
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

async function handleDelete(id) {
  if (!confirm('Удалить пост?')) return
  await postsStore.deletePost(id)
  // Убираем локально, чтобы не сбрасывать уже загруженные страницы
  const index = postsStore.posts.findIndex(p => p.id === id)
  if (index !== -1) postsStore.posts.splice(index, 1)
}
</script>

<template>
  <div>
    <!-- Filters -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
      <div class="flex flex-wrap gap-4">
        <!-- Search -->
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по содержанию..."
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
      @delete="handleDelete"
    />

    <!-- Триггер бесконечной прокрутки -->
    <div ref="loadMoreTrigger" class="h-px" aria-hidden="true"></div>

    <!-- Догрузка -->
    <div
      v-if="loadingMore"
      class="flex items-center justify-center gap-2 py-6 text-gray-500 text-sm"
    >
      <div class="w-5 h-5 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin"></div>
      <span>Загрузка...</span>
    </div>

    <p v-else-if="allLoaded" class="text-center text-gray-400 text-sm py-6">
      Больше постов нет
    </p>
  </div>
</template>
