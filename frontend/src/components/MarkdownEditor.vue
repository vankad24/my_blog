<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
import VueEasyLightbox from 'vue-easy-lightbox'
import 'vue-easy-lightbox/dist/external-css/vue-easy-lightbox.css'

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
const visible = ref(false)
const image = ref('')

function openImage(src) {
  image.value = src
  visible.value = true
}

function handleImageClick(event) {
  const img = event.target.closest('img')
  if (!img || !editorElement.value?.contains(img)) {
    return
  }
  openImage(img.src)
}

function createEditor() {
  if (!editorElement.value) return

  const headers = {
    'X-Requested-With': 'XMLHttpRequest',
  }
  if (authStore.accessToken) {
    headers['Authorization'] = `Bearer ${authStore.accessToken}`
  }

  const my_emoji = {
    // Vditor defaults
    "+1": "👍",
    "-1": "👎",
    "heart": "❤️",
    "cold_sweat": "😰",

    // My list
    "grinning": "😀",
    "smiley": "😃",
    "smile": "😄",
    "sweat_smile": "😅",
    "laughing": "😆",
    "wink": "😉",
    "blush": "😊",
    "heart_eyes": "😍",
    "thinking": "🤔",
    "cry": "😢",
    "sob": "😭",
    "angry": "😠",
    "scream": "😱",
    "sunglasses": "😎",
    "fire": "🔥",
    "rocket": "🚀",
    "tada": "🎉",
    "star": "⭐",
    "100": "💯",
    "check": "✅",
    "joy": "😂",
    "tired": "😫",
    "expressionless": "😑",
    "grin": "😁",
    "partying": "🥳",
    "exploding": "🤯",
    "raised_eyebrow": "🤨",
    "rofl": "🤣",
    "money_mouth": "🤑",
    "moyai": "🗿",
    "video_game": "🎮",
    "drooling": "🤤",
    "stuck_out_tongue_winking_eye": "😜",
    "monocle": "🧐",
    "milk": "🥛",
    "smiling_imp": "😈",
    "moon": "🌚",
    "rose": "🌹",
    "facepalm": "🤦‍♂️",
    "smirk": "😏",
    "see_no_evil": "🙈",
    "flushed": "😳",
    "pray": "🙏",
    "upside_down": "🙃",
    "hand_over_mouth": "🤭",
    "smiling_face_with_hearts": "🥰",
    "cake": "🍰",
    "birthday": "🎂",
    "muscle": "💪",
    "eyes": "👀",
    "neutral_face": "😐",
    "roll_eyes": "🙄",
    "poop": "💩",
    "innocent": "😇",
    "rage": "🤬",
    "skull": "💀",
    "ok_hand": "👌",
    "point_right": "👉",
    "sparkles": "✨",
  };

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
      '|',
      'edit-mode'
    ],
    hint: {
      emoji: my_emoji,
    },
    upload: {
      accept: 'image/*,video/*,audio/*,.pdf,.zip,.doc,.docx,.txt,.csv,.rar,.7z,.gz,.tar',
      multiple: true,
      fieldName: 'file',
      url: '/api/upload/image/',
      headers,
      max: 200 * 1024 * 1024,  // 200MB
    },
    after() {
      // Привязываем обработчик клика после создания редактора
      editorElement.value.addEventListener('click', handleImageClick)
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
    editorElement.value?.removeEventListener('click', handleImageClick)
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
  editorElement.value?.removeEventListener('click', handleImageClick)
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
  <VueEasyLightbox
    :visible="visible"
    :imgs="image"
    @hide="visible = false"
  />
</template>
