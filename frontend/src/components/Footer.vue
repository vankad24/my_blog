<template>
  <footer class="bg-white border-t border-gray-200 mt-32">
    <div class="max-w-5xl mx-auto px-4 py-6">
      <div class="flex justify-between items-center">
        <p class="text-gray-500 text-sm">&copy; {{ new Date().getFullYear() }} Molo4ko production. Все права не защищены.</p>
        <div class="flex space-x-4">
          <router-link to="/privacy" class="text-gray-400 hover:text-gray-600 text-sm">Политика конфиденциальности</router-link>
          <router-link to="/terms" class="text-gray-400 hover:text-gray-600 text-sm">Условия использования</router-link>
        </div>
      </div>
    </div>
  </footer>
</template>