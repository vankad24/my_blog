<script setup>
</script>

<template>
  <div class="text-center pb-16">
    <img src="/not_found.jpg" alt="Not Found" class="max-h-[60vh] w-auto mx-auto mb-4 rounded-lg" />
    <h1 class="text-6xl font-bold text-gray-300 mb-4">404</h1>
    <h2 class="text-2xl font-bold text-gray-900 mb-2">Страница не найдена</h2>
    <p class="text-gray-500 mb-6">Страница, которую вы ищете, не существует или была удалена.</p>
    <router-link to="/" class="text-primary-600 hover:underline font-medium">
      Вернуться на главную →
    </router-link>
  </div>
</template>