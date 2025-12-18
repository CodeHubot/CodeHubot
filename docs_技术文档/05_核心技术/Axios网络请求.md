# Axios 网络请求封装

## 概述

Axios 是一个基于 Promise 的 HTTP 客户端。本文档详细介绍 Axios 在 CodeHubot 项目中的封装和使用，适合教学和实际开发。

## 为什么使用 Axios？

### Axios vs Fetch

| 特性 | Axios | Fetch API |
|------|-------|-----------|
| **浏览器兼容** | IE 11+ ✅ | 需要 polyfill |
| **自动转换 JSON** | 是 ✅ | 否 |
| **拦截器** | 支持 ✅ | 不支持 |
| **取消请求** | 支持 ✅ | 需要 AbortController |
| **超时控制** | 支持 ✅ | 不支持 |
| **进度监听** | 支持 ✅ | 不支持 |

## 基础使用

### 1. 安装

```bash
npm install axios
```

### 2. 基本请求

```javascript
import axios from 'axios'

// GET 请求
axios.get('/api/users')
  .then(response => console.log(response.data))
  .catch(error => console.error(error))

// POST 请求
axios.post('/api/users', {
  name: 'Alice',
  email: 'alice@example.com'
})
  .then(response => console.log(response.data))

// 使用 async/await
async function getUsers() {
  try {
    const response = await axios.get('/api/users')
    console.log(response.data)
  } catch (error) {
    console.error(error)
  }
}
```

## CodeHubot 封装实践

### 1. request.js 封装

**文件位置**: `frontend/src/utils/request.js`

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',  // API 基础路径
  timeout: 30000,   // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// ========== 请求拦截器 ==========
request.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    
    // 添加 Token
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    
    // 打印请求信息（开发环境）
    if (import.meta.env.DEV) {
      console.log('📤 Request:', {
        url: config.url,
        method: config.method,
        params: config.params,
        data: config.data
      })
    }
    
    return config
  },
  error => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// ========== 响应拦截器 ==========
request.interceptors.response.use(
  response => {
    // 打印响应信息（开发环境）
    if (import.meta.env.DEV) {
      console.log('📥 Response:', response.data)
    }
    
    const { data } = response
    
    // 统一响应格式处理
    if (data.success || data.code === 200) {
      return data
    } else {
      // 业务错误
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
  },
  async error => {
    const { response, config } = error
    
    if (!response) {
      // 网络错误
      ElMessage.error('网络错误，请检查网络连接')
      return Promise.reject(error)
    }
    
    const { status } = response
    
    // 401 Token 过期
    if (status === 401 && !config._retry) {
      config._retry = true
      
      try {
        const authStore = useAuthStore()
        const newToken = await authStore.refreshTokenAction()
        
        // 使用新 Token 重试请求
        config.headers.Authorization = `Bearer ${newToken}`
        return request(config)
      } catch (refreshError) {
        // 刷新失败，跳转登录
        const authStore = useAuthStore()
        authStore.logout()
        router.push('/login')
        return Promise.reject(refreshError)
      }
    }
    
    // 403 无权限
    if (status === 403) {
      ElMessage.error('无权访问')
      router.push('/403')
    }
    
    // 404 Not Found
    if (status === 404) {
      ElMessage.error('请求的资源不存在')
    }
    
    // 500 服务器错误
    if (status === 500) {
      ElMessage.error('服务器错误')
    }
    
    // 其他错误
    const errorMessage = response.data?.message || '请求失败'
    ElMessage.error(errorMessage)
    
    return Promise.reject(error)
  }
)

export default request
```

### 2. API 接口定义

**文件位置**: `frontend/src/api/device.js`

```javascript
import request from '@/utils/request'

/**
 * 获取设备列表
 * @param {Object} params - 查询参数
 * @param {Number} params.page - 页码
 * @param {Number} params.size - 每页数量
 * @returns {Promise}
 */
export function getDeviceList(params) {
  return request({
    url: '/devices',
    method: 'get',
    params
  })
}

/**
 * 获取设备详情
 * @param {Number} id - 设备ID
 * @returns {Promise}
 */
export function getDeviceDetail(id) {
  return request({
    url: `/devices/${id}`,
    method: 'get'
  })
}

/**
 * 创建设备
 * @param {Object} data - 设备数据
 * @returns {Promise}
 */
export function createDevice(data) {
  return request({
    url: '/devices',
    method: 'post',
    data
  })
}

/**
 * 更新设备
 * @param {Number} id - 设备ID
 * @param {Object} data - 更新数据
 * @returns {Promise}
 */
export function updateDevice(id, data) {
  return request({
    url: `/devices/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除设备
 * @param {Number} id - 设备ID
 * @returns {Promise}
 */
export function deleteDevice(id) {
  return request({
    url: `/devices/${id}`,
    method: 'delete'
  })
}

/**
 * 控制设备
 * @param {Number} id - 设备ID
 * @param {Object} data - 控制指令
 * @returns {Promise}
 */
export function controlDevice(id, data) {
  return request({
    url: `/devices/${id}/control`,
    method: 'post',
    data
  })
}
```

### 3. 在组件中使用

```vue
<template>
  <div>
    <el-button @click="fetchDevices" :loading="loading">
      刷新
    </el-button>
    
    <el-table :data="devices" v-loading="loading">
      <el-table-column prop="name" label="设备名称" />
      <el-table-column prop="device_type" label="设备类型" />
      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button @click="handleControl(row)">控制</el-button>
          <el-button @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  getDeviceList, 
  controlDevice, 
  deleteDevice 
} from '@/api/device'

const devices = ref([])
const loading = ref(false)

// 获取设备列表
const fetchDevices = async () => {
  loading.value = true
  try {
    const response = await getDeviceList({ page: 1, size: 20 })
    devices.value = response.data
  } catch (error) {
    console.error('获取设备列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 控制设备
const handleControl = async (device) => {
  try {
    await controlDevice(device.id, {
      command: 'turn_on'
    })
    ElMessage.success('控制成功')
  } catch (error) {
    console.error('控制失败:', error)
  }
}

// 删除设备
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该设备吗？', '提示', {
      type: 'warning'
    })
    
    await deleteDevice(id)
    ElMessage.success('删除成功')
    fetchDevices()  // 刷新列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 初始化
fetchDevices()
</script>
```

## 高级功能

### 1. 请求取消

```javascript
import { ref } from 'vue'

// 创建取消令牌
const cancelTokenSource = axios.CancelToken.source()

// 发起可取消的请求
async function fetchData() {
  try {
    const response = await axios.get('/api/data', {
      cancelToken: cancelTokenSource.token
    })
    return response.data
  } catch (error) {
    if (axios.isCancel(error)) {
      console.log('请求已取消:', error.message)
    } else {
      throw error
    }
  }
}

// 取消请求
function cancelRequest() {
  cancelTokenSource.cancel('用户取消了请求')
}

// 组件卸载时取消
onUnmounted(() => {
  cancelRequest()
})
```

### 2. 并发请求

```javascript
// 并发多个请求
async function fetchAll() {
  try {
    const [users, devices, courses] = await Promise.all([
      axios.get('/api/users'),
      axios.get('/api/devices'),
      axios.get('/api/courses')
    ])
    
    return {
      users: users.data,
      devices: devices.data,
      courses: courses.data
    }
  } catch (error) {
    console.error('请求失败:', error)
  }
}
```

### 3. 上传文件

```javascript
/**
 * 上传文件
 * @param {File} file - 文件对象
 * @param {Function} onProgress - 进度回调
 * @returns {Promise}
 */
export function uploadFile(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request({
    url: '/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      const percent = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      )
      onProgress && onProgress(percent)
    }
  })
}
```

```vue
<template>
  <el-upload
    :on-change="handleFileChange"
    :auto-upload="false"
  >
    <el-button>选择文件</el-button>
  </el-upload>
  
  <el-progress 
    v-if="uploading" 
    :percentage="uploadProgress" 
  />
</template>

<script setup>
import { ref } from 'vue'
import { uploadFile } from '@/api/upload'

const uploading = ref(false)
const uploadProgress = ref(0)

const handleFileChange = async (file) => {
  uploading.value = true
  uploadProgress.value = 0
  
  try {
    await uploadFile(file.raw, (percent) => {
      uploadProgress.value = percent
    })
    
    ElMessage.success('上传成功')
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}
</script>
```

### 4. 下载文件

```javascript
/**
 * 下载文件
 * @param {String} url - 文件URL
 * @param {String} filename - 文件名
 * @returns {Promise}
 */
export async function downloadFile(url, filename) {
  const response = await request({
    url,
    method: 'get',
    responseType: 'blob'  // 重要！
  })
  
  // 创建下载链接
  const blob = new Blob([response])
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}
```

## 请求重试

```javascript
// 添加重试拦截器
axios.interceptors.response.use(null, async (error) => {
  const config = error.config
  
  // 设置重试次数
  if (!config || !config.retry) {
    return Promise.reject(error)
  }
  
  config.__retryCount = config.__retryCount || 0
  
  if (config.__retryCount >= config.retry) {
    return Promise.reject(error)
  }
  
  config.__retryCount += 1
  
  // 延迟重试
  const delay = config.retryDelay || 1000
  await new Promise(resolve => setTimeout(resolve, delay))
  
  return axios(config)
})

// 使用
axios.get('/api/data', {
  retry: 3,          // 重试3次
  retryDelay: 1000   // 延迟1秒
})
```

## 环境配置

```javascript
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 可选：重写路径
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

```bash
# .env.development
VITE_API_BASE_URL=/api

# .env.production
VITE_API_BASE_URL=https://api.example.com/api
```

```javascript
// utils/request.js
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000
})
```

## 最佳实践

### 1. 统一错误处理

```javascript
// utils/errorHandler.js
export function handleError(error) {
  if (error.response) {
    // 服务器返回错误状态码
    const { status, data } = error.response
    
    switch (status) {
      case 400:
        ElMessage.error(data.message || '请求参数错误')
        break
      case 401:
        ElMessage.error('未授权，请重新登录')
        router.push('/login')
        break
      case 403:
        ElMessage.error('无权访问')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 500:
        ElMessage.error('服务器错误')
        break
      default:
        ElMessage.error(data.message || '请求失败')
    }
  } else if (error.request) {
    // 请求已发出但没有收到响应
    ElMessage.error('网络错误，请检查网络连接')
  } else {
    // 其他错误
    ElMessage.error(error.message || '未知错误')
  }
}
```

### 2. Loading 状态管理

```javascript
// composables/useRequest.js
import { ref } from 'vue'

export function useRequest(apiFunc) {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)
  
  const execute = async (...args) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiFunc(...args)
      data.value = response.data
      return response
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }
  
  return {
    loading,
    error,
    data,
    execute
  }
}

// 使用
const { loading, data, execute } = useRequest(getDeviceList)

// 调用
await execute({ page: 1, size: 20 })
```

### 3. API 模块化

```
api/
├── index.js        # 导出所有 API
├── auth.js         # 认证相关
├── user.js         # 用户相关
├── device.js       # 设备相关
└── course.js       # 课程相关
```

```javascript
// api/index.js
export * from './auth'
export * from './user'
export * from './device'
export * from './course'

// 使用
import { login, getDeviceList, getUserInfo } from '@/api'
```

## 教学要点总结

### 核心概念
1. **HTTP 客户端**: Axios 实例
2. **拦截器**: 请求/响应拦截
3. **统一封装**: request.js
4. **API 模块化**: 按业务划分
5. **错误处理**: 统一处理

### 实用技能
- ✅ Axios 基本使用
- ✅ 请求/响应拦截器
- ✅ Token 自动刷新
- ✅ 文件上传下载
- ✅ 请求取消和重试

### 最佳实践
- ✅ 统一的 request 封装
- ✅ API 模块化管理
- ✅ 完善的错误处理
- ✅ Loading 状态管理
- ✅ 环境变量配置

## 相关文档

- [前端架构](../02_系统架构/前端架构.md) - 前端架构设计
- [API测试](../04_开发调试/API测试.md) - API 接口测试
- [常见问题排查](../04_开发调试/常见问题排查.md) - 请求问题排查
