<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import TagSelector from '@/components/TagSelector.vue'

const route = useRoute()
const router = useRouter()
const postsStore = usePostsStore()

const form = ref({
  title: '',
  content: '',
  tags: [],
})
const loading = ref(true)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    await postsStore.fetchPost(route.params.id)
    const post = postsStore.currentPost
    if (!post) {
      router.push('/')
      return
    }
    form.value = {
      title: post.title,
      content: post.content,
      tags: post.tags?.map(t => t.id) || [],
    }
    postsStore.fetchTags()
  } catch {
    router.push('/')
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  error.value = ''
  if (!form.value.title.trim() || !form.value.content.trim()) {
    error.value = 'Заголовок и содержание обязательны'
    return
  }

  saving.value = true
  try {
    const data = {
      title: form.value.title,
      content: form.value.content,
      tags: form.value.tags,
    }
    const post = await postsStore.updatePost(route.params.id, data)
    router.push({ name: 'PostDetail', params: { id: post.id } })
  } catch (err) {
    if (err.response?.data) {
      error.value = Object.values(err.response.data).flat().join('; ')
    } else {
      error.value = 'Ошибка обновления поста'
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-8 bg-gray-200 rounded w-1/3"></div>
      <div class="h-64 bg-gray-200 rounded"></div>
    </div>

    <div v-else>
      <h1 class="text-2xl font-bold text-gray-900 mb-6">Редактирование поста</h1>

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
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Содержание</label>
          <MarkdownEditor
            v-model="form.content"
            :cache-id="`post-${route.params.id}`"
            placeholder="Напишите пост в Markdown..."
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Теги</label>
          <TagSelector v-model="form.tags" />
        </div>

        <div class="flex justify-end space-x-2">
          <router-link
            :to="{ name: 'PostDetail', params: { id: route.params.id } }"
            class="text-gray-600 border border-gray-300 px-4 py-2.5 rounded-lg hover:bg-gray-50 transition-colors font-medium"
          >
            Отмена
          </router-link>
          <button
            type="submit"
            :disabled="saving"
            class="bg-primary-600 text-white px-6 py-2.5 rounded-lg hover:bg-primary-700 transition-colors font-medium disabled:opacity-50"
          >
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>