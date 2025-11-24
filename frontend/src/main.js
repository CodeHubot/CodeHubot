import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { useUserStore } from './store/user'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 初始化用户认证状态
const userStore = useUserStore()
userStore.initializeAuth()

// 设置页面标题
const appTitle = import.meta.env.VITE_APP_TITLE || '物联网设备服务系统'
document.title = appTitle

app.mount('#app')
