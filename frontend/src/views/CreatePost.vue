<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePostsStore } from '@/stores/posts'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import TagSelector from '@/components/TagSelector.vue'

const router = useRouter()
const postsStore = usePostsStore()
const editorRef = ref(null)

const form = ref({
  content: '',
  tags: [],
})
const loading = ref(false)
const error = ref('')

onMounted(() => {
  postsStore.fetchTags()
})

async function handleSubmit() {
  error.value = ''
  if (!form.value.content.trim()) {
    error.value = 'Содержание обязательно'
    return
  }

  loading.value = true
  try {
    const data = {
      content: form.value.content,
      tags: form.value.tags,
    }
    const post = await postsStore.createPost(data)
    // Важно: сначала очищаем локальный кэш, затем редактор
    editorRef.value?.clear()
    router.push({ name: 'PostDetail', params: { id: post.id } })
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
        <label class="block text-sm font-medium text-gray-700 mb-1">Теги</label>
        <TagSelector v-model="form.tags" />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Содержание</label>
        <MarkdownEditor
          ref="editorRef"
          v-model="form.content"
          cache-id="post-new"
          placeholder="Напишите пост в Markdown..."
        />
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