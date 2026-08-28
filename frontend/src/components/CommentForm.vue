<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import MarkdownEditor from '@/components/MarkdownEditor.vue'

const props = defineProps({
  postId: {
    type: Number,
    required: true,
  },
})

const emit = defineEmits(['submitted'])
const authStore = useAuthStore()
const body = ref('')
const submitting = ref(false)
const editorRef = ref(null)

async function handleSubmit() {
  if (!body.value.trim()) return
  submitting.value = true
  try {
    emit('submitted', {
      body: body.value,
      content_type_str: 'posts.post',
      object_id: props.postId,
    })
    editorRef.value?.clear()
    body.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div v-if="authStore.isAuthenticated" class="mt-6">
    <form @submit.prevent="handleSubmit">
      <MarkdownEditor
        ref="editorRef"
        v-model="body"
        :cache-id="`comment-${postId}`"
        :height="'200px'"
        placeholder="Напишите Markdown текст..."
      />
      <div class="flex justify-end mt-2">
        <button
          type="submit"
          :disabled="submitting || !body.trim()"
          class="btn-primary disabled:opacity-50"
        >
          {{ submitting ? 'Отправка...' : 'Отправить' }}
        </button>
      </div>
    </form>
  </div>
  <div v-else class="mt-6 text-center">
    <router-link to="/login" class="text-primary-600 hover:underline">Войдите</router-link>, чтобы оставить комментарий
  </div>
</template>

<style scoped>
.btn-primary {
  @apply bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors font-medium text-sm;
}
</style>