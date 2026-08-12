<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'

const router = useRouter()
const postsStore = usePostsStore()

const form = ref({
  title: '',
  content: '',
  excerpt: '',
  category: null,
  tags: [],
})
const loading = ref(false)
const error = ref('')

onMounted(() => {
  postsStore.fetchCategories()
  postsStore.fetchTags()
})

async function handleSubmit() {
  error.value = ''
  if (!form.value.title.trim() || !form.value.content.trim()) {
    error.value = 'Заголовок и содержание обязательны'
    return
  }

  loading.value = true
  try {
    const data = {
      title: form.value.title,
      content: form.value.content,
      excerpt: form.value.excerpt,
      category: form.value.category || undefined,
      tags: form.value.tags,
    }
    const post = await postsStore.createPost(data)
    router.push({ name: 'PostDetail', params: { slug: post.slug } })
  } catch (err) {
    console.error('[CreatePost] Ошибка создания поста:', err)
    if (err.response?.data) {
      error.value = Object.values(err.response.data).flat().join('; ')
    } else {
      error.value = 'Ошибка создания поста'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Новый пост</h1>

    <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-4">
      {{ error }}
    </div>

    <form @submit.prevent="handleSubmit" class="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Заголовок</label>
        <input
          v-model="form.title"
          type="text"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent text-lg"
          placeholder="Заголовок поста"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Краткое описание</label>
        <textarea
          v-model="form.excerpt"
          rows="2"
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          placeholder="Краткое описание (необязательно)"
        ></textarea>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Категория</label>
          <select
            v-model="form.category"
            class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          >
            <option :value="null">Без категории</option>
            <option
              v-for="cat in postsStore.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Теги</label>
          <select
            v-model="form.tags"
            multiple
            class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent h-20"
          >
            <option
              v-for="tag in postsStore.tags"
              :key="tag.id"
              :value="tag.slug"
            >
              #{{ tag.name }}
            </option>
          </select>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Содержание</label>
        <textarea
          v-model="form.content"
          rows="15"
          required
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
          placeholder="HTML-содержание поста..."
        ></textarea>
      </div>

      <div class="flex justify-end">
        <button
          type="submit"
          :disabled="loading"
          class="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:opacity-50"
        >
          {{ loading ? 'Публикация...' : 'Опубликовать' }}
        </button>
      </div>
    </form>
  </div>
</template>