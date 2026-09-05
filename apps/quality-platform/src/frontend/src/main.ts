import { createApp } from 'vue'
import App from './App.vue'
import router from './app/router'
import './styles/tokens.css'
import './styles/base.css'
import './features/collaboration/collaboration.css'
import './features/gongzuo/gongzuo.css'

createApp(App).use(router).mount('#app')
