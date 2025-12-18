# Vue 3 组合式 API 深度解析

## 概述

Vue 3 引入了组合式 API (Composition API)，这是一种全新的编写 Vue 组件的方式。本文档深入讲解组合式 API 的核心概念和在 CodeHubot 项目中的实际应用。

## 为什么需要组合式 API？

### 选项式 API 的局限性

```vue
<!-- ❌ 选项式 API (Vue 2) -->
<script>
export default {
  data() {
    return {
      user: null,
      devices: [],
      loading: false
    }
  },
  computed: {
    deviceCount() {
      return this.devices.length
    }
  },
  methods: {
    fetchUser() { /* ... */ },
    fetchDevices() { /* ... */ }
  },
  mounted() {
    this.fetchUser()
    this.fetchDevices()
  }
}
</script>

问题：
1. 逻辑分散：同一个功能的代码分散在 data、methods、computed 等选项中
2. 复用困难：跨组件复用逻辑需要 mixins（容易产生命名冲突）
3. 类型推断弱：TypeScript 支持不够好
```

### 组合式 API 的优势

```vue
<!-- ✅ 组合式 API (Vue 3) -->
<script setup>
import { ref, computed, onMounted } from 'vue'

// 用户相关逻辑集中
const user = ref(null)
const fetchUser = async () => { /* ... */ }

// 设备相关逻辑集中
const devices = ref([])
const deviceCount = computed(() => devices.value.length)
const fetchDevices = async () => { /* ... */ }

// 生命周期
onMounted(() => {
  fetchUser()
  fetchDevices()
})
</script>

优势：
✅ 逻辑集中：相关代码写在一起
✅ 易于复用：提取为可组合函数
✅ 类型推断好：TypeScript 友好
✅ 代码更简洁：<script setup> 语法糖
```

## 核心 API

### 1. 响应式基础 API

#### ref - 基本类型响应式

```vue
<script setup>
import { ref } from 'vue'

// 创建响应式引用
const count = ref(0)          // 数字
const message = ref('Hello')  // 字符串
const isActive = ref(true)    // 布尔值
const user = ref(null)        // 对象引用

// 读取值：需要 .value
console.log(count.value)  // 0

// 修改值
count.value++
message.value = 'World'

// 在模板中自动解包，不需要 .value
</script>

<template>
  <div>
    <!-- 自动解包 -->
    <p>{{ count }}</p>
    <p>{{ message }}</p>
    
    <button @click="count++">增加</button>
  </div>
</template>
```

#### reactive - 对象响应式

```vue
<script setup>
import { reactive } from 'vue'

// 创建响应式对象
const state = reactive({
  user: {
    name: 'Alice',
    age: 25
  },
  devices: [],
  settings: {
    theme: 'dark',
    language: 'zh-CN'
  }
})

// 直接访问属性（不需要 .value）
console.log(state.user.name)  // 'Alice'

// 修改属性
state.user.age = 26
state.devices.push({ id: 1, name: 'Device 1' })

// ⚠️ 注意：不能替换整个对象
// state = { ... }  // ❌ 会丢失响应式

// ✅ 正确做法：
Object.assign(state.user, { name: 'Bob', age: 30 })
</script>

<template>
  <div>
    <p>姓名：{{ state.user.name }}</p>
    <p>年龄：{{ state.user.age }}</p>
    <p>设备数：{{ state.devices.length }}</p>
  </div>
</template>
```

#### ref vs reactive 对比

```javascript
// ref：适合基本类型和单一对象引用
const count = ref(0)
const user = ref({ name: 'Alice' })

// 访问需要 .value
count.value++
user.value.name = 'Bob'

// reactive：适合复杂对象
const state = reactive({
  count: 0,
  user: { name: 'Alice' }
})

// 直接访问属性
state.count++
state.user.name = 'Bob'

// ⚠️ 选择建议
// 1. 基本类型：用 ref
// 2. 对象：都可以，但 reactive 更简洁
// 3. 需要整个替换对象：用 ref
```

### 2. 计算属性 computed

```vue
<script setup>
import { ref, computed } from 'vue'

const firstName = ref('张')
const lastName = ref('三')

// 只读计算属性
const fullName = computed(() => {
  return firstName.value + lastName.value
})

// 可写计算属性
const fullNameWritable = computed({
  get() {
    return firstName.value + lastName.value
  },
  set(value) {
    [firstName.value, lastName.value] = value.split('')
  }
})

// 使用
console.log(fullName.value)  // "张三"
fullNameWritable.value = '李四'  // firstName='李', lastName='四'
</script>

<template>
  <div>
    <input v-model="firstName">
    <input v-model="lastName">
    <p>全名：{{ fullName }}</p>
  </div>
</template>
```

#### 计算属性缓存

```javascript
// ✅ 计算属性：有缓存，依赖不变不重新计算
const expensiveResult = computed(() => {
  console.log('执行计算')
  return heavyComputation()
})

// ❌ 方法：每次调用都执行
const expensiveMethod = () => {
  console.log('执行计算')
  return heavyComputation()
}

// 在模板中
// {{ expensiveResult }}  - 只计算一次（依赖不变）
// {{ expensiveMethod() }} - 每次渲染都计算
```

### 3. 侦听器 watch / watchEffect

#### watch - 侦听特定数据源

```vue
<script setup>
import { ref, watch } from 'vue'

const count = ref(0)
const user = ref({ name: 'Alice', age: 25 })

// 侦听单个 ref
watch(count, (newValue, oldValue) => {
  console.log(`count 从 ${oldValue} 变为 ${newValue}`)
})

// 侦听多个数据源
watch([count, user], ([newCount, newUser], [oldCount, oldUser]) => {
  console.log('count 或 user 变化了')
})

// 侦听对象属性（需要 getter 函数）
watch(
  () => user.value.age,
  (newAge, oldAge) => {
    console.log(`年龄从 ${oldAge} 变为 ${newAge}`)
  }
)

// 深度侦听对象
watch(
  user,
  (newUser, oldUser) => {
    console.log('user 对象内部发生变化')
  },
  { deep: true }  // 深度侦听
)

// 立即执行
watch(
  count,
  (value) => {
    console.log('当前值:', value)
  },
  { immediate: true }  // 立即执行一次
)
</script>
```

#### watchEffect - 自动追踪依赖

```vue
<script setup>
import { ref, watchEffect } from 'vue'

const count = ref(0)
const user = ref({ name: 'Alice' })

// 自动追踪依赖（函数内用到的响应式数据）
watchEffect(() => {
  console.log(`count: ${count.value}, name: ${user.value.name}`)
  // 当 count 或 user.name 变化时，自动重新执行
})

// 停止侦听
const stop = watchEffect(() => {
  console.log(count.value)
})

// 手动停止
stop()

// 清理副作用
watchEffect((onCleanup) => {
  const timer = setTimeout(() => {
    console.log('延迟执行')
  }, 1000)
  
  // 在副作用重新执行前清理
  onCleanup(() => {
    clearTimeout(timer)
  })
})
</script>
```

#### watch vs watchEffect 对比

```javascript
// watch：明确指定侦听的数据源
watch(
  () => user.value.age,  // 明确侦听 age
  (newAge) => { /* ... */ }
)

// watchEffect：自动追踪依赖
watchEffect(() => {
  // 函数内用到的所有响应式数据都会被追踪
  console.log(user.value.age)
  console.log(count.value)
})

// 选择建议：
// - watch：需要访问旧值、或需要延迟执行
// - watchEffect：简单的副作用，自动追踪更方便
```

### 4. 生命周期钩子

```vue
<script setup>
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted
} from 'vue'

// 挂载前
onBeforeMount(() => {
  console.log('组件即将挂载')
})

// 挂载后（最常用）
onMounted(() => {
  console.log('组件已挂载')
  // 适合：
  // - 访问 DOM
  // - 发起网络请求
  // - 初始化第三方库
})

// 更新前
onBeforeUpdate(() => {
  console.log('组件即将更新')
})

// 更新后
onUpdated(() => {
  console.log('组件已更新')
  // ⚠️ 避免在此修改状态，可能导致无限循环
})

// 卸载前
onBeforeUnmount(() => {
  console.log('组件即将卸载')
})

// 卸载后
onUnmounted(() => {
  console.log('组件已卸载')
  // 适合：
  // - 清理定时器
  // - 取消网络请求
  // - 移除事件监听
})
</script>
```

#### 生命周期对比（选项式 vs 组合式）

| 选项式 API | 组合式 API |
|-----------|-----------|
| beforeCreate | ❌ 不需要（setup 中直接写） |
| created | ❌ 不需要（setup 中直接写） |
| beforeMount | onBeforeMount |
| mounted | onMounted |
| beforeUpdate | onBeforeUpdate |
| updated | onUpdated |
| beforeUnmount | onBeforeUnmount |
| unmounted | onUnmounted |

### 5. 模板引用 ref

```vue
<script setup>
import { ref, onMounted } from 'vue'

// 创建模板引用
const inputRef = ref(null)
const listRef = ref([])

onMounted(() => {
  // 访问 DOM 元素
  inputRef.value.focus()
  
  // 访问组件实例
  console.log(listRef.value)
})
</script>

<template>
  <div>
    <!-- 绑定到元素 -->
    <input ref="inputRef" type="text">
    
    <!-- 绑定到组件 -->
    <MyList ref="listRef" />
    
    <!-- v-for 中的 ref（会收集到数组中） -->
    <div v-for="item in items" :key="item.id">
      <input :ref="el => listRef.push(el)">
    </div>
  </div>
</template>
```

## 组合式函数 (Composables)

### 什么是组合式函数？

```javascript
// 可复用的状态逻辑封装
// composables/useCounter.js
import { ref, computed } from 'vue'

export function useCounter(initialValue = 0) {
  const count = ref(initialValue)
  
  const double = computed(() => count.value * 2)
  
  const increment = () => {
    count.value++
  }
  
  const decrement = () => {
    count.value--
  }
  
  return {
    count,
    double,
    increment,
    decrement
  }
}
```

### 使用组合式函数

```vue
<script setup>
import { useCounter } from '@/composables/useCounter'

// 使用组合式函数
const { count, double, increment, decrement } = useCounter(10)

// 可以创建多个独立实例
const counter1 = useCounter(0)
const counter2 = useCounter(100)
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <p>Double: {{ double }}</p>
    <button @click="increment">+</button>
    <button @click="decrement">-</button>
  </div>
</template>
```

### 实用组合式函数示例

#### useFetch - 数据获取

```javascript
// composables/useFetch.js
import { ref } from 'vue'

export function useFetch(url) {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(false)
  
  const fetchData = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(url)
      data.value = await response.json()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  }
  
  // 立即执行
  fetchData()
  
  return { data, error, loading, refetch: fetchData }
}

// 使用
const { data, error, loading, refetch } = useFetch('/api/users')
```

#### usePermission - 权限检查

```javascript
// composables/usePermission.js
import { computed } from 'vue'

export function usePermission() {
  const userInfo = computed(() => {
    const info = localStorage.getItem('user_info')
    return info ? JSON.parse(info) : {}
  })
  
  const hasPermission = (roles) => {
    const userRole = userInfo.value.role
    return roles.includes(userRole)
  }
  
  const isAdmin = computed(() => userInfo.value.role === 'admin')
  const isTeacher = computed(() => userInfo.value.role === 'teacher')
  
  return {
    userInfo,
    hasPermission,
    isAdmin,
    isTeacher
  }
}

// 使用
const { isAdmin, hasPermission } = usePermission()
```

#### useLocalStorage - 本地存储

```javascript
// composables/useLocalStorage.js
import { ref, watch } from 'vue'

export function useLocalStorage(key, defaultValue) {
  // 从 localStorage 读取初始值
  const storedValue = localStorage.getItem(key)
  const data = ref(storedValue ? JSON.parse(storedValue) : defaultValue)
  
  // 监听变化，自动保存
  watch(
    data,
    (newValue) => {
      localStorage.setItem(key, JSON.stringify(newValue))
    },
    { deep: true }
  )
  
  return data
}

// 使用
const theme = useLocalStorage('theme', 'light')
theme.value = 'dark'  // 自动保存到 localStorage
```

## CodeHubot 项目实践

### 组件结构

```vue
<!-- AdminDashboard.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

// 路由
const router = useRouter()

// 响应式数据
const stats = ref({
  users: 0,
  devices: 0,
  courses: 0
})
const loading = ref(false)

// 计算属性
const totalItems = computed(() => {
  return stats.value.users + stats.value.devices + stats.value.courses
})

// 方法
const fetchStats = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/dashboard/stats')
    const data = await response.json()
    stats.value = data
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

const navigateTo = (path) => {
  router.push(path)
}

// 生命周期
onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="dashboard">
    <h1>管理后台</h1>
    
    <div v-if="loading" class="loading">加载中...</div>
    
    <div v-else class="stats">
      <div class="stat-card" @click="navigateTo('/users')">
        <h3>用户数</h3>
        <p>{{ stats.users }}</p>
      </div>
      
      <div class="stat-card" @click="navigateTo('/devices')">
        <h3>设备数</h3>
        <p>{{ stats.devices }}</p>
      </div>
      
      <div class="stat-card" @click="navigateTo('/courses')">
        <h3>课程数</h3>
        <p>{{ stats.courses }}</p>
      </div>
      
      <div class="stat-card">
        <h3>总计</h3>
        <p>{{ totalItems }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
</style>
```

### 提取可复用逻辑

```javascript
// composables/useDeviceManagement.js
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export function useDeviceManagement() {
  const devices = ref([])
  const loading = ref(false)
  
  const fetchDevices = async () => {
    loading.value = true
    try {
      const response = await fetch('/api/devices')
      const data = await response.json()
      devices.value = data.data
    } catch (error) {
      ElMessage.error('获取设备列表失败')
    } finally {
      loading.value = false
    }
  }
  
  const deleteDevice = async (deviceId) => {
    try {
      await fetch(`/api/devices/${deviceId}`, { method: 'DELETE' })
      ElMessage.success('删除成功')
      // 刷新列表
      await fetchDevices()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }
  
  return {
    devices,
    loading,
    fetchDevices,
    deleteDevice
  }
}
```

## 最佳实践

### 1. 命名规范

```javascript
// ✅ 好的命名
const userList = ref([])
const isLoading = ref(false)
const fetchUserData = async () => {}
const handleSubmit = () => {}

// ❌ 不好的命名
const data = ref([])  // 太泛化
const flag = ref(false)  // 不明确
const func1 = () => {}  // 无意义
```

### 2. 响应式数据组织

```javascript
// ✅ 按功能组织
// 用户相关
const user = ref(null)
const userLoading = ref(false)
const fetchUser = async () => {}

// 设备相关
const devices = ref([])
const devicesLoading = ref(false)
const fetchDevices = async () => {}

// ❌ 混乱组织
const data1 = ref(null)
const data2 = ref([])
const loading1 = ref(false)
const loading2 = ref(false)
```

### 3. 组合式函数规范

```javascript
// ✅ 好的组合式函数
export function useAuth() {
  const user = ref(null)
  const login = async (credentials) => { /* ... */ }
  const logout = () => { /* ... */ }
  
  // 返回响应式数据和方法
  return {
    user,
    login,
    logout
  }
}

// ❌ 不要返回普通值
export function useAuth() {
  const user = ref({ name: 'Alice' })
  
  // ❌ 返回 .value，会丢失响应式
  return {
    user: user.value
  }
}
```

## 教学要点总结

### 核心概念
1. **ref / reactive**：创建响应式数据
2. **computed**：计算属性，有缓存
3. **watch / watchEffect**：侦听数据变化
4. **生命周期钩子**：组件生命周期管理
5. **组合式函数**：提取可复用逻辑

### 对比选项式 API
| 特性 | 选项式 API | 组合式 API |
|------|-----------|-----------|
| 代码组织 | 按选项类型 | 按逻辑功能 |
| 逻辑复用 | Mixins | 组合式函数 |
| TypeScript | 一般 | 优秀 |
| 学习曲线 | 平缓 | 稍陡 |

### 迁移建议
- 新项目：直接使用组合式 API
- 旧项目：可以混用，逐步迁移
- 小组件：选项式 API 也 OK
- 复杂逻辑：组合式 API 更好

## 相关文档

- [Pinia状态管理](./Pinia状态管理.md) - 全局状态管理
- [Vue Router路由](./VueRouter路由.md) - 路由管理
- [前端架构](../02_系统架构/前端架构.md) - 项目架构
