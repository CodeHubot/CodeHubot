/**
 * Axios 统一配置和拦截器
 * 处理所有API请求的统一格式、认证、错误处理
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',  // 统一的API基础路径
  timeout: 30000,   // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// ============================================================================
// 请求拦截器 - 在发送请求之前做统一处理
// ============================================================================
request.interceptors.request.use(
  config => {
    // 自动添加认证令牌
    const token = localStorage.getItem('admin_access_token') || 
                  localStorage.getItem('access_token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 可以在这里添加其他通用请求头
    // config.headers['X-Custom-Header'] = 'value'
    
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// ============================================================================
// 响应拦截器 - 统一处理响应格式和错误
// ============================================================================
request.interceptors.response.use(
  response => {
    const res = response.data
    
    // 统一处理两种响应格式：
    // 格式1: { success: true, data: {...}, message: '' }
    // 格式2: { code: 200, data: {...}, message: '' }
    
    const isSuccess = res.success === true || res.code === 200
    
    if (isSuccess) {
      // 请求成功，返回统一格式
      return {
        success: true,
        data: res.data,
        message: res.message || res.msg || '',
        originalResponse: response
      }
    } else {
      // 业务逻辑错误
      const errorMsg = res.message || res.msg || '请求失败'
      ElMessage.error(errorMsg)
      
      return Promise.reject({
        success: false,
        message: errorMsg,
        code: res.code || res.status,
        data: null
      })
    }
  },
  error => {
    console.error('响应错误:', error)
    
    // HTTP错误处理
    let message = '请求失败'
    
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          message = data.message || data.detail || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          // 清除token并跳转到登录页
          localStorage.removeItem('admin_access_token')
          localStorage.removeItem('access_token')
          router.push('/login')
          break
        case 403:
          message = '没有权限访问该资源'
          break
        case 404:
          message = data.message || data.detail || '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务暂时不可用'
          break
        default:
          message = data.message || data.detail || `请求失败 (${status})`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    } else {
      message = error.message || '请求配置错误'
    }
    
    ElMessage.error(message)
    
    return Promise.reject({
      success: false,
      message,
      code: error.response?.status,
      error
    })
  }
)

// ============================================================================
// 导出封装好的请求方法
// ============================================================================

/**
 * GET 请求
 * @param {string} url - 请求路径
 * @param {object} params - 查询参数
 * @param {object} config - axios配置
 * @returns {Promise}
 */
export function get(url, params = {}, config = {}) {
  return request.get(url, { params, ...config })
}

/**
 * POST 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @param {object} config - axios配置
 * @returns {Promise}
 */
export function post(url, data = {}, config = {}) {
  return request.post(url, data, config)
}

/**
 * PUT 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @param {object} config - axios配置
 * @returns {Promise}
 */
export function put(url, data = {}, config = {}) {
  return request.put(url, data, config)
}

/**
 * PATCH 请求
 * @param {string} url - 请求路径
 * @param {object} data - 请求体数据
 * @param {object} config - axios配置
 * @returns {Promise}
 */
export function patch(url, data = {}, config = {}) {
  return request.patch(url, data, config)
}

/**
 * DELETE 请求
 * @param {string} url - 请求路径
 * @param {object} params - 查询参数
 * @param {object} config - axios配置
 * @returns {Promise}
 */
export function del(url, params = {}, config = {}) {
  return request.delete(url, { params, ...config })
}

/**
 * 上传文件
 * @param {string} url - 请求路径
 * @param {FormData} formData - 表单数据
 * @param {function} onProgress - 上传进度回调
 * @returns {Promise}
 */
export function upload(url, formData, onProgress) {
  return request.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      if (onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(percent)
      }
    }
  })
}

/**
 * 下载文件
 * @param {string} url - 请求路径
 * @param {string} filename - 文件名
 * @param {object} params - 查询参数
 * @returns {Promise}
 */
export function download(url, filename, params = {}) {
  return request.get(url, {
    params,
    responseType: 'blob'
  }).then(response => {
    const blob = new Blob([response.data])
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  })
}

// 默认导出request实例（用于特殊场景）
export default request
