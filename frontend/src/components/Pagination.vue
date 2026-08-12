<script setup>
defineProps({
  currentPage: {
    type: Number,
    default: 1,
  },
  totalPages: {
    type: Number,
    default: 1,
  },
})

const emit = defineEmits(['page-change'])
</script>

<template>
  <div v-if="totalPages > 1" class="flex justify-center items-center space-x-2 mt-8">
    <button
      :disabled="currentPage <= 1"
      @click="emit('page-change', currentPage - 1)"
      class="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
    >
      ← Назад
    </button>
    <span
      v-for="page in totalPages"
      :key="page"
      @click="emit('page-change', page)"
      class="px-3 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors"
      :class="page === currentPage ? 'bg-primary-600 text-white' : 'hover:bg-gray-100'"
    >
      {{ page }}
    </span>
    <button
      :disabled="currentPage >= totalPages"
      @click="emit('page-change', currentPage + 1)"
      class="px-3 py-2 rounded-lg border border-gray-300 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
    >
      Вперед →
    </button>
  </div>
</template>