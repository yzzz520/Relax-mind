import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { retryPendingCapsules } from './api/capsuleQueue'
import { useAuthStore } from './stores/auth'
import './assets/styles/tokens.css'

async function bootstrap() {
  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  const auth = useAuthStore(pinia)
  await auth.initialize()
  app.use(router)
  app.mount('#app')
  void retryPendingCapsules(auth.user?.id)
}

bootstrap()
