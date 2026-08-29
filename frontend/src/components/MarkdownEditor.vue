<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

const authStore = useAuthStore()

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Напишите Markdown текст...',
  },
  cacheId: {
    type: String,
    default: 'post-new',
  },
  mode: {
    type: String,
    default: 'sv',
  },
  height: {
    type: String,
    default: '500px',
  },
})

const content = defineModel({ type: String, default: '' })

const editorElement = ref(null)
let editor = null

function createEditor() {
  if (!editorElement.value) return

  const headers = {
    'X-Requested-With': 'XMLHttpRequest',
  }
  if (authStore.accessToken) {
    headers['Authorization'] = `Bearer ${authStore.accessToken}`
  }

  editor = new Vditor(editorElement.value, {
    value: content.value || '',
    mode: props.mode,
    height: props.height,
    lang: 'ru_RU',
    placeholder: props.placeholder,
    cache: {
      enable: true,
      id: props.cacheId,
    },
    preview: {
      markdown: {
        sanitize: true,
      },
    },
    toolbar: [
      'headings',
      'bold',
      'italic',
      'strike',
      '|',
      'quote',
      'list',
      'ordered-list',
      'check',
      'code',
      'inline-code',
      'link',
      'table',
      'upload',
      '|',
      'emoji',
      'preview',
      'fullscreen',
    ],
    upload: {
      accept: 'image/*,video/*,audio/*,.pdf,.zip,.doc,.docx,.txt,.csv,.rar,.7z,.gz,.tar',
      multiple: true,
      fieldName: 'file',
      url: '/api/upload/image/',
      headers,
      max: 200 * 1024 * 1024,  // 200MB
    },
    input(value) {
      content.value = value
    },
  })
}

// Если токен обновился (например, через refresh), пересоздаём редактор
// чтобы upload-хедеры содержали актуальный токен
watch(() => authStore.accessToken, () => {
  if (editor) {
    editor.destroy()
    editor = null
  }
  createEditor()
})

onMounted(() => {
  createEditor()
})

// Синхронизация при асинхронной загрузке значения извне (например, из API).
// Не пересоздаём редактор — только setValue.
watch(content, (value) => {
  if (!editor) return
  if (editor.getValue() !== value) {
    editor.setValue(value)
  }
})

onBeforeUnmount(() => {
  editor?.destroy()
  editor = null
})

// Публичный метод для очистки кэша и редактора после успешной публикации
function clear() {
  editor?.clearCache()
  editor?.setValue('')
}

defineExpose({ clear })
</script>

<template>
  <div ref="editorElement"></div>
</template>
