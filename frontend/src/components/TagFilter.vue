<script setup>
import { ref, onMounted } from 'vue'
import { usePostsStore } from '@/stores/posts'
import TagChip from '@/components/TagChip.vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])

const postsStore = usePostsStore()
const showDropdown = ref(false)

const selectedTag = ref(null)

onMounted(async () => {
  if (postsStore.tags.length === 0) {
    await postsStore.fetchTags()
  }
  // Восстановить выбранный тег из props
  if (props.modelValue) {
    selectedTag.value = postsStore.tags.find(t => t.id == props.modelValue) || null
  }
})

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value && postsStore.tags.length === 0) {
    postsStore.fetchTags()
  }
}

function selectTag(tag) {
  selectedTag.value = tag
  emit('update:modelValue', tag.id)
  showDropdown.value = false
}

function clearFilter() {
  selectedTag.value = null
  emit('update:modelValue', '')
}

function closeDropdown() {
  showDropdown.value = false
}
</script>

<template>
  <div class="relative">
    <!-- Выбранный тег + кнопка -->
    <div class="flex items-center gap-2">
      <div v-if="selectedTag" class="flex items-center gap-2">
        <TagChip :name="selectedTag.name" :active="true" />
        <button
          @click="clearFilter"
          class="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Кнопка "Фильтр" -->
      <div class="relative">
        <button
          @click="toggleDropdown"
          class="inline-flex items-center gap-1.5 px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Фильтр
        </button>

        <!-- Dropdown -->
        <div
          v-if="showDropdown"
          @clickoutside="closeDropdown"
          class="absolute z-20 left-0 mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
        >
          <!-- Список тегов -->
          <div class="max-h-60 overflow-y-auto">
            <button
              v-for="tag in postsStore.tags"
              :key="tag.id"
              @click="selectTag(tag)"
              class="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <TagChip :name="tag.name" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
