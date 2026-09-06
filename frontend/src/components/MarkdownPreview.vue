<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import VueEasyLightbox from 'vue-easy-lightbox'
import 'vue-easy-lightbox/dist/external-css/vue-easy-lightbox.css'

const props = defineProps({
  markdown: {
    type: String,
    default: '',
  },
})

const html = ref('')
const containerRef = ref(null)
const visible = ref(false)
const image = ref('')

const VIDEO_EXTS = ['.mp4', '.webm', '.ogg', '.avi', '.mkv', '.mov']
const AUDIO_EXTS = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']

function openImage(src) {
  image.value = src
  visible.value = true
}

function handleImageClick(event) {
  const img = event.target.closest('img')
  if (!img || !containerRef.value?.contains(img)) {
    return
  }
  openImage(img.src)
}

function convertMediaLinks() {
  if (!containerRef.value) return

  // Конвертация ссылок на видео в <video> теги
  containerRef.value.querySelectorAll('a').forEach((link) => {
    const href = link.getAttribute('href') || ''
    const ext = href.substring(href.lastIndexOf('.')).toLowerCase()

    if (VIDEO_EXTS.includes(ext)) {
      const video = document.createElement('video')
      video.controls = true
      video.preload = 'metadata'
      video.className = 'max-w-full rounded-lg shadow-sm'
      const source = document.createElement('source')
      source.src = href
      video.appendChild(source)
      link.replaceWith(video)
    } else if (AUDIO_EXTS.includes(ext)) {
      const audio = document.createElement('audio')
      audio.controls = true
      audio.preload = 'metadata'
      audio.className = 'w-full mt-2 mb-2'
      const source = document.createElement('source')
      source.src = href
      audio.appendChild(source)
      link.replaceWith(audio)
    }
  })
}

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
      await nextTick()
      convertMediaLinks()
    } catch (err) {
      console.error('[MarkdownPreview] Ошибка рендеринга:', err)
      html.value = ''
    }
  },
  { immediate: true },
)

watch(
  () => html.value,
  async () => {
    await nextTick()
    // Перепривязываем обработчик после обновления HTML
    if (containerRef.value) {
      containerRef.value.removeEventListener('click', handleImageClick)
      containerRef.value.addEventListener('click', handleImageClick)
    }
  },
)

onBeforeUnmount(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('click', handleImageClick)
  }
})
</script>

<template>
  <div ref="containerRef" class="markdown-preview vditor-reset break-words" v-html="html"></div>
  <VueEasyLightbox
    :visible="visible"
    :imgs="image"
    @hide="visible = false"
  />
</template>

<style scoped>
/* Стили для ссылок на файлы (PDF, ZIP и т.д.) */
.markdown-preview :deep(a) {
  @apply inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium;
}

.markdown-preview :deep(a) svg {
  @apply w-4 h-4 flex-shrink-0;
}

.markdown-preview :deep(img) {
  @apply cursor-pointer hover:opacity-90 transition-opacity;
}
</style>
