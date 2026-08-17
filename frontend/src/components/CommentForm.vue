<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

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

async function handleSubmit() {
  if (!body.value.trim()) return
  submitting.value = true
  try {
    emit('submitted', {
      body: body.value,
      content_type_str: 'posts.post',
      object_id: props.postId,
    })
    body.value = ''
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div v-if="authStore.isAuthenticated" class="mt-6">
    <form @submit.prevent="handleSubmit">
      <textarea
        v-model="body"
        rows="3"
        class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
        placeholder="Напишите комментарий..."
        required
      ></textarea>
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