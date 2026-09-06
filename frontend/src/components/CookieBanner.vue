<script setup>
import { ref, onMounted } from 'vue'

const accepted = ref(false)

onMounted(() => {
  if (localStorage.getItem('cookie-notice-accepted') === '1') {
    accepted.value = true
  }
})

function accept() {
  localStorage.setItem('cookie-notice-accepted', '1')
  accepted.value = true
}
</script>

<template>
  <div
    v-if="!accepted"
    class="fixed bottom-5 left-1/2 -translate-x-1/2 z-[1000] max-w-4xl w-full flex items-center justify-between gap-4 px-5 py-4 bg-white text-gray-900 rounded-xl shadow-xl border-2 border-gray-300"
  >
    <span class="text-lg font-medium">Мы используем cookies🍪 для работы сайта и вы ничего не можете с этим поделать.</span>
    <button
      @click="accept"
      class="shrink-0 px-5 py-2.5 text-base font-semibold text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
    >
      Понятно
    </button>
  </div>
</template>
