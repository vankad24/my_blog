<script setup>
import { ref, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

const props = defineProps({
  markdown: {
    type: String,
    default: '',
  },
})

const html = ref('')

watch(
  () => props.markdown,
  async (value) => {
    if (!value) {
      html.value = ''
      return
    }
    try {
      html.value = await Vditor.md2html(value, {
        mode: 'light',
        preview: {
          markdown: {
            sanitize: true,
          },
        },
      })
    } catch (err) {
      console.error('[MarkdownPreview] Ошибка рендеринга:', err)
      html.value = ''
    }
  },
  { immediate: true },
)
</script>

<template>
  <div class="markdown-preview vditor-reset break-words" v-html="html"></div>
</template>
