import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

// Перехватчик ошибок Vue — только для dev-сборки
if (import.meta.env.DEV) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('[Vue error]:', err)
    if (info) console.error('[Vue error] info:', info)
  }
}

// Инициализируем аутентификацию до монтирования приложения
const authStore = useAuthStore(pinia)
authStore.init().finally(() => {
  app.mount('#app')
})
