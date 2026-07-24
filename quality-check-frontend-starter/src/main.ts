import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from '@/App.vue'
import { router } from '@/app/router'
import '@/styles/tokens.css'
import '@/styles/base.css'
import 'gridstack/dist/gridstack.min.css'

createApp(App).use(createPinia()).use(router).mount('#app')
