import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'
import logger from '../utils/logger'

// 创建axios实例
// 使用环境变量配置 API 地址，如果没有配置则使用默认值
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'
const timeout = import.meta.env.VITE_API_TIMEOUT ? parseInt(import.meta.env.VITE_API_TIMEOUT) : 10000

const request = axios.create({
  baseURL,
  timeout
})

// 验证token格式
const isValidTokenFormat = (token) => {
  if (!token) return false
  const parts = token.split('.')
  return parts.length === 3
}

// 请求拦截器
request.interceptors.request.use(
  config => {
    const userStore = useUserStore()
    
    logger.api(config.method, config.url, config.data)
    
    if (userStore.token) {
      // 先检查token格式
      if (!isValidTokenFormat(userStore.token)) {
        logger.error('Token格式无效，清除并登出')
        userStore.logout('Token格式无效')
        ElMessage.error('登录信息无效，请重新登录')
        
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(new Error('Token format invalid'))
      }
      
      // 检查token是否过期
      if (userStore.isTokenExpired) {
        logger.warn('Token已过期，尝试自动刷新')
        // 不阻塞请求，让响应拦截器处理401并自动刷新
      } else {
        config.headers.Authorization = `Bearer ${userStore.token}`
        logger.debug('已添加Authorization头')
      }
      
      // 即使过期也添加header，让后端返回401触发自动刷新
      if (!config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${userStore.token}`
      }
    } else {
      logger.debug('未找到token，匿名请求')
    }
    return config
  },
  error => {
    logger.error('API请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 存储正在等待的请求队列（当token正在刷新时）
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// 响应拦截器
request.interceptors.response.use(
  response => {
    logger.apiResponse(response.status, response.config.url, response.data)
    return response
  },
  async error => {
    const originalRequest = error.config
    const status = error.response?.status
    const url = originalRequest?.url
    
    logger.error('API响应错误:', {
      url,
      status,
      message: error.message
    })
    
    // 处理401错误 - 尝试刷新token
    if (status === 401 && !originalRequest._retry) {
      // 如果是refresh端点失败，直接登出
      if (url?.includes('/auth/refresh')) {
        logger.error('Refresh token失败，执行登出')
        const userStore = useUserStore()
        userStore.logout('Token刷新失败')
        ElMessage.error('登录已过期，请重新登录')
        
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
      
      // 标记此请求已重试过
      originalRequest._retry = true
      
      if (isRefreshing) {
        // 如果正在刷新token，将请求加入队列
        logger.debug('Token刷新中，请求加入队列')
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return request(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }
      
      // 开始刷新token
      isRefreshing = true
      const userStore = useUserStore()
      
      try {
        logger.info('🔄 检测到401错误，尝试刷新token')
        const newToken = await userStore.refreshAccessToken()
        
        if (newToken) {
          // 刷新成功，更新请求头并重试
          logger.info('✅ Token刷新成功，重试原请求')
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          processQueue(null, newToken)
          return request(originalRequest)
        } else {
          // 刷新失败，登出
          throw new Error('Token刷新失败')
        }
      } catch (err) {
        logger.error('Token刷新失败，执行登出')
        processQueue(err, null)
        userStore.logout('认证失败')
        ElMessage.error('登录已过期，请重新登录')
        
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
        return Promise.reject(err)
      } finally {
        isRefreshing = false
      }
    } else if (error.message === 'Token expired') {
      logger.warn('Token过期错误')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else if (status >= 400) {
      // 对于注册接口，不在这里显示错误，让 store 中的错误处理来处理
      // 这样可以避免注册成功但显示错误的问题
      if (!url?.includes('/auth/register')) {
        ElMessage.error(error.response?.data?.detail || '请求失败')
      }
    }
    
    return Promise.reject(error)
  }
)

export default request
