<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePostsStore } from '@/stores/posts'
import { stringToHslColor } from '@/utils/stringToHslColor'
import TagChip from '@/components/TagChip.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue'])

const postsStore = usePostsStore()

const showDropdown = ref(false)
const showNewTagInput = ref(false)
const newTagName = ref('')
const isLoading = ref(false)

const selectedTags = computed(() => {
  return props.modelValue.map(id => ({
    id,
    name: postsStore.tags.find(t => t.id === id)?.name || `Тег #${id}`,
  }))
})

const availableTags = computed(() => {
  return postsStore.tags.filter(tag => !props.modelValue.includes(tag.id))
})

function getTagColor(name) {
  return stringToHslColor(name)
}

function getTagTextColor(name) {
  const hue = parseInt(stringToHslColor(name).match(/\d+/)[0])
  return `hsl(${hue}, 60%, 30%)`
}

onMounted(async () => {
  if (postsStore.tags.length === 0) {
    await postsStore.fetchTags()
  }
})

function toggleDropdown() {
  showDropdown.value = !showDropdown.value
  if (showDropdown.value && postsStore.tags.length === 0) {
    postsStore.fetchTags()
  }
}

function addTag(tagId) {
  if (!props.modelValue.includes(tagId)) {
    emit('update:modelValue', [...props.modelValue, tagId])
  }
  showNewTagInput.value = false
}

function removeTag(tagId) {
  emit('update:modelValue', props.modelValue.filter(id => id !== tagId))
}

async function createTag() {
  const name = newTagName.value.trim()
  if (!name) return
  isLoading.value = true
  try {
    const tag = await postsStore.createTag(name)
    emit('update:modelValue', [...props.modelValue, tag.id])
    newTagName.value = ''
    showNewTagInput.value = false
    // Обновить список тегов
    await postsStore.fetchTags()
  } catch (err) {
    console.error('[TagSelector] Ошибка создания тега:', err)
  } finally {
    isLoading.value = false
  }
}

function closeDropdown() {
  showDropdown.value = false
}
</script>

<template>
  <div class="relative">
    <!-- Теги-чипсы + кнопка -->
    <div class="flex flex-wrap items-center gap-1.5 min-h-[40px]">
      <span
        v-for="tag in selectedTags"
        :key="tag.id"
        class="inline-flex items-center gap-1.5"
      >
        <TagChip :name="tag.name" :active="true" />
        <button
          @click="removeTag(tag.id)"
          class="ml-0.5 opacity-60 hover:opacity-100 transition-opacity"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </span>

      <!-- Кнопка "Добавить" -->
      <div class="relative">
        <button
          @click="toggleDropdown"
          class="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          Тег
        </button>

        <!-- Dropdown -->
        <div
          v-if="showDropdown"
          @clickoutside="closeDropdown"
          class="absolute z-20 right-0 mt-2 w-64 bg-white border border-gray-200 rounded-xl shadow-lg overflow-hidden"
        >
          <!-- Список тегов -->
          <div class="max-h-60 overflow-y-auto">
            <button
              v-for="tag in availableTags"
              :key="tag.id"
              @click="addTag(tag.id)"
              class="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors"
            >
              <TagChip :name="tag.name" />
            </button>

            <!-- Кнопка "Добавить тег" -->
            <button
              v-if="!showNewTagInput"
              @click="showNewTagInput = true"
              class="w-full text-left px-4 py-2.5 text-sm text-gray-500 hover:bg-gray-50 transition-colors border-t border-gray-100"
            >
              + Добавить тег
            </button>
          </div>

          <!-- Форма создания нового тега -->
          <div v-if="showNewTagInput" class="p-3 border-t border-gray-100">
            <input
              v-model="newTagName"
              type="text"
              placeholder="Название тега..."
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent mb-2"
              @keydown.enter="createTag"
            />
            <div class="flex gap-2">
              <button
                @click="createTag"
                :disabled="!newTagName.trim() || isLoading"
                class="flex-1 bg-primary-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {{ isLoading ? 'Создание...' : 'Создать' }}
              </button>
              <button
                @click="showNewTagInput = false"
                class="px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
