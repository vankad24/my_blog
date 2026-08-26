<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

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

onMounted(() => {
  if (!editorElement.value) return
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
      '|',
      'emoji',
      'preview',
      'fullscreen',
    ],
    input(value) {
      content.value = value
    },
  })
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
