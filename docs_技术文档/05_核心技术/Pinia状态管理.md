# Pinia 状态管理详解

## 概述

Pinia 是 Vue 3 官方推荐的状态管理库，是 Vuex 的继任者。本文档详细介绍 Pinia 在 CodeHubot 项目中的使用，适合教学和实际开发。

## 为什么使用 Pinia？

### Pinia vs Vuex

| 特性 | Pinia | Vuex 4 |
|------|-------|--------|
| **类型推导** | 优秀 ✅ | 一般 |
| **组合式API** | 原生支持 ✅ | 需要适配 |
| **模块化** | 自动 ✅ | 手动命名空间 |
| **DevTools** | 完整支持 ✅ | 支持 |
| **体积** | 更小 ✅ | 较大 |
| **学习曲线** | 更平缓 ✅ | 较陡 |

### Pinia 的优势

```javascript
// ✅ Pinia - 简洁直观
const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const increment = () => count.value++
  return { count, increment }
})

// ❌ Vuex - 繁琐
const store = createStore({
  state: () => ({ count: 0 }),
  mutations: {
    increment(state) { state.count++ }
  },
  actions: {
    increment(context) { context.commit('increment') }
  }
})
```

## 核心概念

### 1. Store

Store 是保存状态和业务逻辑的实体。

```javascript
// stores/counter.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCounterStore = defineStore('counter', () => {
  // 状态 (State)
  const count = ref(0)
  
  // 计算属性 (Getters)
  const doubleCount = computed(() => count.value * 2)
  
  // 方法 (Actions)
  function increment() {
    count.value++
  }
  
  async function incrementAsync() {
    await new Promise(resolve => setTimeout(resolve, 1000))
    count.value++
  }
  
  return {
    // 导出
    count,
    doubleCount,
    increment,
    incrementAsync
  }
})
```

### 2. 在组件中使用

```vue
<template>
  <div>
    <p>Count: {{ counter.count }}</p>
    <p>Double: {{ counter.doubleCount }}</p>
    <button @click="counter.increment()">增加</button>
  </div>
</template>

<script setup>
import { useCounterStore } from '@/stores/counter'

const counter = useCounterStore()
</script>
```

### 3. 解构使用

```vue
<script setup>
import { storeToRefs } from 'pinia'
import { useCounterStore } from '@/stores/counter'

const counter = useCounterStore()

// ✅ 使用 storeToRefs 保持响应性
const { count, doubleCount } = storeToRefs(counter)

// ✅ 方法可以直接解构
const { increment, incrementAsync } = counter
</script>
```

## CodeHubot 项目实践

### 1. 认证 Store

**文件位置**: `frontend/src/stores/auth.js`

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // ========== 状态 ==========
  const token = ref(null)
  const userInfo = ref(null)
  const loading = ref(false)
  
  // ========== 计算属性 ==========
  const isAuthenticated = computed(() => !!token.value)
  const userRole = computed(() => userInfo.value?.role || '')
  const userName = computed(() => userInfo.value?.name || '')
  
  // 角色判断
  const isStudent = computed(() => userRole.value === 'student')
  const isTeacher = computed(() => userRole.value === 'teacher')
  const isAdmin = computed(() => userRole.value === 'admin')
  
  // ========== 方法 ==========
  
  /**
   * 登录
   */
  async function login(credentials) {
    loading.value = true
    try {
      const response = await loginApi(credentials)
      
      // 保存 token
      token.value = response.data.access_token
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      // 保存用户信息
      userInfo.value = response.data.user
      localStorage.setItem('user_info', JSON.stringify(response.data.user))
      
      return response
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 登出
   */
  async function logout() {
    try {
      await logoutApi()
    } finally {
      // 清除状态
      token.value = null
      userInfo.value = null
      
      // 清除本地存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
    }
  }
  
  /**
   * 初始化（从 localStorage 恢复）
   */
  function init() {
    const storedToken = localStorage.getItem('access_token')
    const storedUser = localStorage.getItem('user_info')
    
    if (storedToken) {
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        userInfo.value = JSON.parse(storedUser)
      } catch (e) {
        console.error('解析用户信息失败:', e)
      }
    }
  }
  
  /**
   * 刷新用户信息
   */
  async function refreshUserInfo() {
    const response = await getUserInfoApi()
    userInfo.value = response.data
    localStorage.setItem('user_info', JSON.stringify(response.data))
  }
  
  return {
    // 状态
    token,
    userInfo,
    loading,
    // 计算属性
    isAuthenticated,
    userRole,
    userName,
    isStudent,
    isTeacher,
    isAdmin,
    // 方法
    login,
    logout,
    init,
    refreshUserInfo
  }
})
```

### 2. 在组件中使用

```vue
<!-- views/Login.vue -->
<template>
  <el-form @submit.prevent="handleLogin">
    <el-form-item>
      <el-input v-model="loginForm.email" placeholder="邮箱" />
    </el-form-item>
    <el-form-item>
      <el-input v-model="loginForm.password" type="password" placeholder="密码" />
    </el-form-item>
    <el-form-item>
      <el-button 
        type="primary" 
        native-type="submit"
        :loading="authStore.loading"
      >
        登录
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = reactive({
  email: '',
  password: ''
})

const handleLogin = async () => {
  try {
    await authStore.login(loginForm)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  }
}
</script>
```

### 3. 权限控制

```vue
<template>
  <div>
    <!-- 仅管理员可见 -->
    <el-button v-if="authStore.isAdmin" @click="deleteUser">
      删除用户
    </el-button>
    
    <!-- 教师和管理员可见 -->
    <el-button v-if="authStore.isTeacher || authStore.isAdmin">
      管理班级
    </el-button>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>
```

## 组合多个 Store

```javascript
// stores/device.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'  // 引入其他 Store

export const useDeviceStore = defineStore('device', () => {
  const authStore = useAuthStore()  // 使用其他 Store
  
  const devices = ref([])
  
  async function fetchDevices() {
    // 可以访问 authStore 的状态
    const userId = authStore.userInfo?.id
    
    const response = await getDevicesApi({ userId })
    devices.value = response.data
  }
  
  return {
    devices,
    fetchDevices
  }
})
```

## 持久化

### 1. 手动持久化

```javascript
export const useUserStore = defineStore('user', () => {
  const preferences = ref({
    theme: 'light',
    language: 'zh-CN'
  })
  
  // 从 localStorage 恢复
  function loadPreferences() {
    const stored = localStorage.getItem('user_preferences')
    if (stored) {
      preferences.value = JSON.parse(stored)
    }
  }
  
  // 保存到 localStorage
  function savePreferences() {
    localStorage.setItem('user_preferences', JSON.stringify(preferences.value))
  }
  
  // 监听变化自动保存
  watch(preferences, savePreferences, { deep: true })
  
  return {
    preferences,
    loadPreferences
  }
})
```

### 2. 使用插件（推荐）

```bash
npm install pinia-plugin-persistedstate
```

```javascript
// main.js
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)
```

```javascript
// stores/user.js
export const useUserStore = defineStore('user', () => {
  const name = ref('')
  const age = ref(0)
  
  return { name, age }
}, {
  persist: true  // 启用持久化
})

// 或自定义持久化
}, {
  persist: {
    key: 'my-custom-key',
    storage: sessionStorage,  // 使用 sessionStorage
    paths: ['name']  // 只持久化 name
  }
})
```

## 最佳实践

### 1. Store 命名规范

```javascript
// ✅ 使用 use 前缀 + 名称 + Store 后缀
export const useAuthStore = defineStore('auth', ...)
export const useUserStore = defineStore('user', ...)
export const useDeviceStore = defineStore('device', ...)

// ❌ 不好的命名
export const authStore = defineStore('auth', ...)
export const Auth = defineStore('auth', ...)
```

### 2. Store 职责单一

```javascript
// ✅ 职责单一
const useAuthStore = defineStore('auth', () => {
  // 只管理认证相关状态
})

const useUserStore = defineStore('user', () => {
  // 只管理用户信息
})

// ❌ 职责过多
const useAppStore = defineStore('app', () => {
  // 既管理认证，又管理用户，还管理设备...
})
```

### 3. 合理使用计算属性

```javascript
// ✅ 使用 computed
const doubleCount = computed(() => count.value * 2)

// ❌ 使用 getter 函数（Vuex 风格）
function getDoubleCount() {
  return count.value * 2
}
```

### 4. 异步操作使用 async/await

```javascript
// ✅ 使用 async/await
async function fetchData() {
  loading.value = true
  try {
    const response = await api.getData()
    data.value = response.data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// ❌ 使用 Promise.then
function fetchData() {
  loading.value = true
  api.getData().then(response => {
    data.value = response.data
    loading.value = false
  })
}
```

## 调试

### 1. Vue DevTools

```
安装 Vue DevTools 扩展后：
1. 打开浏览器开发者工具
2. 切换到 Vue 标签页
3. 选择 Pinia 图标
4. 查看所有 Store 的状态
5. 支持时间旅行调试
```

### 2. 日志输出

```javascript
export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)
  
  // 监听状态变化
  watch(token, (newVal, oldVal) => {
    console.log('Token 变化:', { oldVal, newVal })
  })
  
  function setToken(newToken) {
    console.log('设置 Token:', newToken)
    token.value = newToken
  }
  
  return { token, setToken }
})
```

## 教学要点总结

### 核心概念
1. **State**: 响应式状态 (ref/reactive)
2. **Getters**: 计算属性 (computed)
3. **Actions**: 方法 (function)
4. **Store**: 状态容器 (defineStore)

### 使用技巧
- ✅ storeToRefs 保持响应性
- ✅ 组合多个 Store
- ✅ 持久化状态
- ✅ TypeScript 类型推导
- ✅ DevTools 调试

### 最佳实践
- ✅ 职责单一
- ✅ 合理命名
- ✅ 使用组合式 API
- ✅ 异步操作规范
- ✅ 状态持久化

## 相关文档

- [Vue3组合式API](./Vue3组合式API.md) - Composition API 详解
- [前端架构](../02_系统架构/前端架构.md) - 前端架构设计
- [Vue Router路由](./VueRouter路由.md) - 路由管理
